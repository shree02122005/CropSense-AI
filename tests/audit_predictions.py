"""
audit_predictions.py
────────────────────
Standalone root-cause audit script for crop prediction model.
Evaluates model behavior across Karnataka locations and representative weather scenarios
to analyze class dominance (e.g., Grapes), out-of-distribution (OOD) NPK inputs,
and fallback behavior BEFORE any class filtering.

Does NOT modify or import-modify any application code.
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.npk_lookup import get_nearest_npk, DATA_PATH

# Empirical training feature bounds
TRAINING_RANGES = {
    "N": (5.50, 153.80),
    "P": (3.30, 177.91),
    "K": (3.54, 236.77),
    "temperature": (11.54, 40.50),
    "humidity": (1.76, 100.00),
    "ph": (4.90, 7.76),
    "rainfall": (7.39, 315.58),
}

# Weather scenarios across Karnataka agro-climatic zones
WEATHER_SCENARIOS = [
    {
        "name": "Kharif / Monsoon",
        "temp": 26.0,
        "humidity": 80.0,
        "rainfall": 180.0,
        "ph": 6.5,
        "soil_type": 2,  # loamy
    },
    {
        "name": "Rabi / Post-Monsoon",
        "temp": 23.0,
        "humidity": 65.0,
        "rainfall": 45.0,
        "ph": 6.8,
        "soil_type": 0,  # black
    },
    {
        "name": "Summer / Semi-Arid",
        "temp": 34.0,
        "humidity": 45.0,
        "rainfall": 20.0,
        "ph": 7.2,
        "soil_type": 3,  # red
    },
    {
        "name": "Coastal / High Rainfall",
        "temp": 28.0,
        "humidity": 85.0,
        "rainfall": 260.0,
        "ph": 5.5,
        "soil_type": 1,  # clay
    },
    {
        "name": "Statewide Average",
        "temp": 25.5,
        "humidity": 68.0,
        "rainfall": 105.0,
        "ph": 6.4,
        "soil_type": 2,  # loamy
    },
]


def load_karnataka_grid():
    """Load district reference locations plus a geographic coordinate grid across Karnataka."""
    places_df = pd.read_csv(DATA_PATH)
    locations = []
    
    # 1. District reference locations from lookup table
    for _, row in places_df.iterrows():
        locations.append({
            "name": f"{row['reference_place']} ({row['district']})",
            "lat": float(row["latitude"]),
            "lon": float(row["longitude"]),
            "district": row["district"]
        })
    
    # 2. Additional coordinate grid across Karnataka bounds (11.5°N - 18.5°N, 74.0°E - 78.5°E)
    lat_steps = np.linspace(12.0, 18.0, 7)
    lon_steps = np.linspace(74.5, 78.0, 6)
    for lat in lat_steps:
        for lon in lon_steps:
            locations.append({
                "name": f"Grid ({lat:.2f}N, {lon:.2f}E)",
                "lat": float(lat),
                "lon": float(lon),
                "district": "Grid"
            })
            
    return locations


def run_audit():
    model_path = os.path.join(ROOT_DIR, "models", "crop_model.pkl")
    print(f"Loading production model from: {model_path}")
    model = joblib.load(model_path)
    all_classes = list(model.classes_)
    print(f"Loaded model: {type(model).__name__} with {len(all_classes)} classes:")
    print(all_classes)
    print("=" * 85)

    locations = load_karnataka_grid()
    print(f"Total test locations in grid: {len(locations)}")
    print(f"Total weather scenarios: {len(WEATHER_SCENARIOS)}")
    total_runs = len(locations) * len(WEATHER_SCENARIOS)
    print(f"Total predictions to execute: {total_runs}")
    print("=" * 85)

    records = []
    fallback_hits = 0

    for loc in locations:
        lat = loc["lat"]
        lon = loc["lon"]
        
        # Test NPK lookup
        hit_fallback = False
        try:
            npk_info = get_nearest_npk(lat, lon)
            N = float(npk_info["N"])
            P = float(npk_info["P"])
            K = float(npk_info["K"])
            ref_place = npk_info.get("reference_place", "Unknown")
            dist = npk_info.get("distance_km", 0.0)
        except Exception as e:
            hit_fallback = True
            fallback_hits += 1
            N, P, K = 249.7, 46.8, 180.4
            ref_place = "Statewide fallback"
            dist = 0.0

        is_n_ood = N < TRAINING_RANGES["N"][0] or N > TRAINING_RANGES["N"][1]
        is_p_ood = P < TRAINING_RANGES["P"][0] or P > TRAINING_RANGES["P"][1]
        is_k_ood = K < TRAINING_RANGES["K"][0] or K > TRAINING_RANGES["K"][1]
        is_npk_ood = is_n_ood or is_p_ood or is_k_ood

        for weather in WEATHER_SCENARIOS:
            temp = weather["temp"]
            humidity = weather["humidity"]
            rainfall = weather["rainfall"]
            ph = weather["ph"]
            soil_enc = weather["soil_type"]

            feat = np.array([[N, P, K, temp, humidity, ph, rainfall, soil_enc]])
            proba = model.predict_proba(feat)[0]

            # Raw prediction BEFORE filtering
            top_indices = np.argsort(proba)[::-1]
            top1_class = model.classes_[top_indices[0]]
            top1_conf = float(proba[top_indices[0]])
            top3_classes = [model.classes_[i] for i in top_indices[:3]]
            top3_confs = [float(proba[i]) for i in top_indices[:3]]

            records.append({
                "location": loc["name"],
                "lat": lat,
                "lon": lon,
                "ref_place": ref_place,
                "distance_km": dist,
                "hit_fallback": hit_fallback,
                "N": N,
                "P": P,
                "K": K,
                "temp": temp,
                "humidity": humidity,
                "rainfall": rainfall,
                "ph": ph,
                "soil_type": soil_enc,
                "is_n_ood": is_n_ood,
                "is_p_ood": is_p_ood,
                "is_k_ood": is_k_ood,
                "is_npk_ood": is_npk_ood,
                "top1_class": top1_class,
                "top1_conf": top1_conf,
                "top3_classes": top3_classes,
                "top3_confs": top3_confs,
                "weather_scenario": weather["name"],
            })

    df = pd.DataFrame(records)

    # ── Report 1: Top-1 Frequency Table across all 23 classes ────────────────
    print("\n" + "=" * 85)
    print("  FREQUENCY TABLE: TOP-1 PREDICTIONS ACROSS ALL 23 CLASSES (BEFORE FILTERING)")
    print("=" * 85)
    top1_counts = df["top1_class"].value_counts()
    print(f"{'Rank':<5} {'Class':<16} {'Count':<8} {'Percentage':<12} {'Crop Type'}")
    print("-" * 65)

    FRUITS = {"apple", "banana", "grapes", "mango", "muskmelon", "orange", "papaya", "pomegranate", "watermelon", "coconut"}

    all_23_rows = []
    for rank, (crop, count) in enumerate(top1_counts.items(), 1):
        pct = (count / total_runs) * 100
        crop_type = "Fruit/Tree (Excluded)" if crop.lower() in FRUITS else "Field Crop (Allowed)"
        all_23_rows.append((rank, crop, count, pct, crop_type))
        print(f"{rank:<5} {crop:<16} {count:<8} {pct:>6.2f}%       {crop_type}")

    # Display classes with 0 count
    unpredicted = [c for c in all_classes if c not in top1_counts]
    for c in unpredicted:
        crop_type = "Fruit/Tree (Excluded)" if c.lower() in FRUITS else "Field Crop (Allowed)"
        print(f"-     {c:<16} {0:<8}   0.00%       {crop_type}")

    # ── Report 2: Top-3 Appearance Frequency ────────────────────────────────
    print("\n" + "=" * 85)
    print("  TOP-3 APPEARANCE FREQUENCY (BEFORE FILTERING)")
    print("=" * 85)
    top3_flat = [crop for sublist in df["top3_classes"] for crop in sublist]
    top3_counts = pd.Series(top3_flat).value_counts()
    for rank, (crop, count) in enumerate(top3_counts.items(), 1):
        pct = (count / total_runs) * 100
        crop_type = "Fruit/Tree" if crop.lower() in FRUITS else "Field Crop"
        print(f"{rank:<5} {crop:<16} in {count} runs ({pct:.1f}%) [{crop_type}]")

    # ── Report 3: Out-of-Distribution (OOD) Analysis ─────────────────────────
    print("\n" + "=" * 85)
    print("  OUT-OF-DISTRIBUTION (OOD) NPK STATISTICS")
    print("=" * 85)
    n_ood_pct = (df["is_n_ood"].sum() / total_runs) * 100
    p_ood_pct = (df["is_p_ood"].sum() / total_runs) * 100
    k_ood_pct = (df["is_k_ood"].sum() / total_runs) * 100
    npk_ood_pct = (df["is_npk_ood"].sum() / total_runs) * 100

    print(f"Training Ranges:  N={TRAINING_RANGES['N']}, P={TRAINING_RANGES['P']}, K={TRAINING_RANGES['K']}")
    print(f"Runs with N OOD:   {df['is_n_ood'].sum()} / {total_runs} ({n_ood_pct:.1f}%)")
    print(f"Runs with P OOD:   {df['is_p_ood'].sum()} / {total_runs} ({p_ood_pct:.1f}%)")
    print(f"Runs with K OOD:   {df['is_k_ood'].sum()} / {total_runs} ({k_ood_pct:.1f}%)")
    print(f"Runs with ANY NPK OOD: {df['is_npk_ood'].sum()} / {total_runs} ({npk_ood_pct:.1f}%)")

    # ── Report 4: Fallback Execution Audit ──────────────────────────────────
    print("\n" + "=" * 85)
    print("  NPK LOOKUP & FALLBACK EXECUTION AUDIT")
    print("=" * 85)
    print(f"Total get_nearest_npk lookups: {len(locations)}")
    print(f"Exceptions / fallback hits (249.7 Statewide default): {fallback_hits}")
    print(f"Did get_nearest_npk fail for grid coordinates? {'YES' if fallback_hits > 0 else 'NO (0 failures)'}")
    
    # Check what values exist in the lookup table itself:
    places_df = pd.read_csv(DATA_PATH)
    n_249_count = (places_df["N_model_input"] == 249.7).sum()
    print(f"Entries in lookup CSV with N=249.7: {n_249_count} / {len(places_df)} places")
    print("Note: The 249.7 N value is NOT just an exception fallback; it is stored as the active profile")
    print("      for Bengaluru Urban, Rural, Ramanagara, Chikkaballapur, Kolar, and Tumakuru!")

    # ── Report 5: Grapes Dominance & Correlation with OOD ────────────────────
    print("\n" + "=" * 85)
    print("  GRAPES DOMINANCE & OOD CORRELATION ANALYSIS")
    print("=" * 85)
    grapes_runs = df[df["top1_class"] == "grapes"]
    nongrapes_runs = df[df["top1_class"] != "grapes"]
    grapes_count = len(grapes_runs)
    grapes_pct = (grapes_count / total_runs) * 100

    print(f"Total runs where Grapes is Top-1: {grapes_count} / {total_runs} ({grapes_pct:.1f}%)")
    if grapes_count > 0:
        grapes_n_mean = grapes_runs["N"].mean()
        grapes_p_mean = grapes_runs["P"].mean()
        grapes_k_mean = grapes_runs["K"].mean()
        grapes_conf_mean = grapes_runs["top1_conf"].mean()
        print(f"  Grapes runs average NPK:  N={grapes_n_mean:.1f}, P={grapes_p_mean:.1f}, K={grapes_k_mean:.1f}")
        print(f"  Grapes runs average confidence: {grapes_conf_mean*100:.1f}%")

    if len(nongrapes_runs) > 0:
        other_n_mean = nongrapes_runs["N"].mean()
        other_p_mean = nongrapes_runs["P"].mean()
        other_k_mean = nongrapes_runs["K"].mean()
        other_conf_mean = nongrapes_runs["top1_conf"].mean()
        print(f"  Other runs average NPK:   N={other_n_mean:.1f}, P={other_p_mean:.1f}, K={other_k_mean:.1f}")
        print(f"  Other runs average confidence: {other_conf_mean*100:.1f}%")

    # Cross-tabulation of Top-1 crop vs NPK OOD
    print("\nCross-tabulation (Top-1 Class vs NPK OOD):")
    ct = pd.crosstab(df["top1_class"], df["is_npk_ood"], margins=True)
    print(ct)

    print("\n" + "=" * 85)
    print("  AUDIT COMPLETE")
    print("=" * 85)


if __name__ == "__main__":
    run_audit()
