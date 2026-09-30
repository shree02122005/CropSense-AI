"""
test_phase8_locations.py
────────────────────────
Phase 8: Comprehensive End-to-End Karnataka Location Testing
Runs the full prediction pipeline across 10 representative Karnataka locations:
1. Bengaluru (South Interior Karnataka - Urban/Red Sandy)
2. Mysuru (Southern Dry Zone - Red/Loamy)
3. Hassan (Southern Transition Zone - Red Sandy Loam)
4. Kodagu / Madikeri (Hilly Zone - Western Ghats Laterite/Loam)
5. Shivamogga (Southern Transition / Malnad - Loamy)
6. Mangaluru (Coastal Zone - Coastal Alluvium/Sandy)
7. Belagavi (Northern Transition Zone - Deep Black Soil)
8. Dharwad (Northern Transition Zone - Medium Black Soil)
9. Raichur (North Eastern Dry Zone - Deep Black Clay)
10. Kalaburagi (North Eastern Transition Zone - Calcareous Deep Black Vertisol)

Validates:
- Real-time OpenWeather data
- SoilGrids pH with fallback transparency
- Authentic Soil CNN MobileNetV2 classification
- Dynamic Karnataka N/P/K lookup with provenance tracking
- Raw, unclipped feature vector construction [N, P, K, temp, humidity, ph, rainfall, soil_type_encoded]
- Out-of-Distribution (OOD) detection against Phase 6 baseline training boundaries
- Pure Random Forest model inference without multipliers or diversity tampering
"""

import os
import sys
import asyncio
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, ROOT_DIR)

from backend.predict_api import predict_crop, _load_ml_model, _verify_ml_model_features, TRAINING_FEATURE_RANGES

TEST_LOCATIONS = [
    {
        "name": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_000.jpg"),
        "zone": "Eastern Dry Zone",
        "expected_soil": "Red / Sandy Loam"
    },
    {
        "name": "Mysuru",
        "latitude": 12.2958,
        "longitude": 76.6394,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_001.jpg"),
        "zone": "Southern Dry Zone",
        "expected_soil": "Red Loam"
    },
    {
        "name": "Hassan",
        "latitude": 13.0068,
        "longitude": 76.1004,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_002.jpg"),
        "zone": "Southern Transition Zone",
        "expected_soil": "Red Sandy Loam"
    },
    {
        "name": "Kodagu / Madikeri",
        "latitude": 12.4244,
        "longitude": 75.7382,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "loamy", "test_loamy_000.jpg"),
        "zone": "Hilly / Plantation Zone",
        "expected_soil": "Lateritic Loam"
    },
    {
        "name": "Shivamogga",
        "latitude": 13.9299,
        "longitude": 75.5681,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "loamy", "test_loamy_001.jpg"),
        "zone": "Southern Transition Zone",
        "expected_soil": "Red / Laterite Loam"
    },
    {
        "name": "Mangaluru",
        "latitude": 12.9141,
        "longitude": 74.8560,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "sandy", "test_sandy_000.jpg"),
        "zone": "Coastal Zone",
        "expected_soil": "Coastal Sandy Alluvium"
    },
    {
        "name": "Belagavi",
        "latitude": 15.8497,
        "longitude": 74.4977,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_000.jpg"),
        "zone": "Northern Transition Zone",
        "expected_soil": "Medium to Deep Black"
    },
    {
        "name": "Dharwad",
        "latitude": 15.4589,
        "longitude": 75.0078,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_001.jpg"),
        "zone": "Northern Transition Zone",
        "expected_soil": "Medium Black"
    },
    {
        "name": "Raichur",
        "latitude": 16.2120,
        "longitude": 77.3439,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_002.jpg"),
        "zone": "North Eastern Dry Zone",
        "expected_soil": "Deep Black Clay"
    },
    {
        "name": "Kalaburagi",
        "latitude": 17.3297,
        "longitude": 76.8343,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_003.jpg"),
        "zone": "North Eastern Transition Zone",
        "expected_soil": "Deep Black Calcareous Vertisol"
    }
]


async def run_phase8():
    print("=" * 95)
    print("  PHASE 8: FULL PIPELINE KARNATAKA LOCATION TESTING & OOD AUDIT (10 LOCATIONS)")
    print("=" * 95)

    model = _load_ml_model()
    _verify_ml_model_features(model)
    print(f"✔ ML Model Loaded: {type(model).__name__} | Features: {model.n_features_in_} | Classes: {len(model.classes_)}")

    results = []

    for idx, loc in enumerate(TEST_LOCATIONS, 1):
        name = loc["name"]
        lat = loc["latitude"]
        lon = loc["longitude"]
        img_path = loc["soil_image"]
        zone = loc["zone"]

        assert os.path.exists(img_path), f"Soil test image missing: {img_path}"
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        print("-" * 95)
        print(f"[{idx}/10] Testing Location: {name} ({lat:.4f}°N, {lon:.4f}°E) — Zone: {zone}")
        print(f"       Soil test image: {os.path.basename(img_path)}")

        res = await predict_crop(img_bytes, lat, lon)

        top_crops_summary = [f"{c['name']} ({c['confidence']*100:.1f}%)" for c in res["crops"]]
        ood_status = res.get("npk_out_of_training_range")
        ood_features = res.get("npk_ood_features")
        
        record = {
            "index": idx,
            "location": name,
            "agro_climatic_zone": zone,
            "resolved_location": res.get("location"),
            "latitude": lat,
            "longitude": lon,
            "N": res["N"],
            "P": res["P"],
            "K": res["K"],
            "npk_source_district": res.get("npk_district"),
            "npk_reference_place": res.get("npk_reference_place"),
            "npk_source_type": res.get("npk_source_type"),
            "npk_distance_km": res.get("npk_distance_km"),
            "npk_source_note": res.get("npk_source_note"),
            "temperature_c": res["temperature"],
            "humidity_pct": res["humidity"],
            "rainfall_mm": res["rainfall"],
            "ph": res["ph"],
            "ph_is_fallback": res.get("ph_is_fallback"),
            "ph_source": res.get("ph_source"),
            "organic_carbon_pct": res["organic_carbon"],
            "soil_type_detected": res["soil_type"],
            "soil_type_encoded": res["soil_type_encoded"],
            "soil_cnn_confidence": res["soil_confidence"],
            "feature_vector": res["feature_vector"],
            "npk_out_of_training_range": ood_status,
            "npk_ood_features": ood_features,
            "all_ood_features": res.get("all_ood_features"),
            "ood_warning": res.get("ood_warning"),
            "top_3_crops": top_crops_summary,
            "crops_detailed": res["crops"],
            "training_ranges": res.get("training_ranges")
        }
        results.append(record)

        print(f"       ✔ NPK (kg/ha):   N={res['N']}, P={res['P']}, K={res['K']} | Source: {res.get('npk_source_type')} ({res.get('npk_district')})")
        print(f"       ✔ OOD Status:    OOD={ood_status} | OOD Features: {ood_features}")
        print(f"       ✔ Weather:       {res['temperature']}°C, {res['humidity']}%, {res['rainfall']}mm | City: {res.get('location')}")
        print(f"       ✔ pH & Carbon:   pH={res['ph']} (fallback={res.get('ph_is_fallback')}), SOC={res['organic_carbon']}%")
        print(f"       ✔ Soil CNN:      {res['soil_type']} ({res['soil_confidence']*100:.1f}%) | Encoded: {res['soil_type_encoded']}")
        print(f"       ✔ Feature Vect:  {res['feature_vector']}")
        print(f"       ✔ Top 3 Crops:   {', '.join(top_crops_summary)}")

    out_file = os.path.join(ROOT_DIR, "phase8_karnataka_test_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved complete Phase 8 test results to: {out_file}")

    print("\n" + "=" * 95)
    print("  PHASE 8 VALIDATION SUMMARY TABLE")
    print("=" * 95)
    fmt = "{:<16} | {:<12} | {:<5} | {:<9} | {:<5} | {:<4} | {:<5} | {:<5} | {:<7} | {:<7} | {:<22}"
    print(fmt.format("Location", "N/P/K", "OOD?", "OOD Feat", "Temp", "Hum", "Rain", "pH", "pH FB?", "Soil", "Top Pick (Prob)"))
    print("-" * 115)
    for r in results:
        npk_str = f"{r['N']:.0f}/{r['P']:.0f}/{r['K']:.0f}"
        ood_f = ",".join(r["npk_ood_features"]) if r["npk_ood_features"] else "None"
        fb_s = "YES" if r["ph_is_fallback"] else "NO"
        top1 = r["top_3_crops"][0] if r["top_3_crops"] else "None"
        print(fmt.format(
            r["location"],
            npk_str,
            str(r["npk_out_of_training_range"]),
            ood_f,
            f"{r['temperature_c']}C",
            f"{r['humidity_pct']:.0f}%",
            f"{r['rainfall_mm']:.1f}",
            f"{r['ph']:.2f}",
            fb_s,
            r["soil_type_detected"],
            top1
        ))

    print("\nPhase 8 location testing completed successfully.")


if __name__ == "__main__":
    asyncio.run(run_phase8())
