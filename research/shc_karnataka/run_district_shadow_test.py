import os
import joblib
import numpy as np
import pandas as pd

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V1_PATH = os.path.join(ROOT_DIR, "data", "karnataka_main_places_npk_project_ready_v1.csv")
V2_PATH = os.path.join(ROOT_DIR, "data", "karnataka_main_places_npk_project_ready_v2.csv")
MODEL_PATH = os.path.join(ROOT_DIR, "models", "crop_model.pkl")
OUT_CSV = os.path.join(ROOT_DIR, "research", "shc_karnataka", "shc_model_comparison.csv")

def run_shadow_test():
    print("=" * 70)
    print("PHASE 6: DISTRICT SHADOW TEST (CONTROLLED BENCHMARK)")
    print("=" * 70)

    model = joblib.load(MODEL_PATH)
    classes = model.classes_

    df_v1 = pd.read_csv(V1_PATH)
    df_v2 = pd.read_csv(V2_PATH)

    # Filter 30 administrative districts (and optionally keep coverage row)
    dist_v1 = df_v1[df_v1["district"] != "Karnataka coverage"].copy()
    dist_v2 = df_v2[df_v2["district"] != "Karnataka coverage"].copy()

    merged = pd.merge(
        dist_v1[["district", "reference_place", "latitude", "longitude", "N_model_input", "P_model_input", "K_model_input"]],
        dist_v2[["district", "N_model_input", "P_model_input", "K_model_input"]],
        on="district",
        suffixes=("_old", "_new")
    )

    print(f"Total Administrative Districts Matched: {len(merged)}")

    # Controlled environmental variables (Standard Karnataka Kharif conditions)
    # Explicitly documented:
    # Temperature = 26.0 °C
    # Humidity = 68.0 %
    # pH = 6.5
    # Rainfall = 120.0 mm
    # Soil type encoded = 3 (Red Soil, predominant in Karnataka)
    std_temp = 26.0
    std_humidity = 68.0
    std_ph = 6.5
    std_rainfall = 120.0
    soil_code = 3

    training_n_max = 153.79
    training_p_max = 177.91
    training_k_max = 236.77

    records = []
    n_changed = 0
    n_ood = 0

    for _, row in merged.iterrows():
        dist = row["district"]
        old_n = float(row["N_model_input_old"])
        old_p = float(row["P_model_input_old"])
        old_k = float(row["K_model_input_old"])

        new_n = float(row["N_model_input_new"])
        new_p = float(row["P_model_input_new"])
        new_k = float(row["K_model_input_new"])

        # Predict with old values
        feat_old = np.array([[old_n, old_p, old_k, std_temp, std_humidity, std_ph, std_rainfall, soil_code]])
        proba_old = model.predict_proba(feat_old)[0]
        idx_old = np.argmax(proba_old)
        old_pred = classes[idx_old]
        old_conf = float(proba_old[idx_old])

        # Predict with new values
        feat_new = np.array([[new_n, new_p, new_k, std_temp, std_humidity, std_ph, std_rainfall, soil_code]])
        proba_new = model.predict_proba(feat_new)[0]
        idx_new = np.argmax(proba_new)
        new_pred = classes[idx_new]
        new_conf = float(proba_new[idx_new])

        changed = "yes" if old_pred != new_pred else "no"
        if changed == "yes":
            n_changed += 1

        is_ood_n = new_n > training_n_max
        is_ood_k = new_k > training_k_max
        is_ood = is_ood_n or is_ood_k
        if is_ood:
            n_ood += 1

        records.append({
            "district": dist,
            "old_N": round(old_n, 1),
            "old_P": round(old_p, 1),
            "old_K": round(old_k, 1),
            "new_N": round(new_n, 1),
            "new_P": round(new_p, 1),
            "new_K": round(new_k, 1),
            "old_prediction": old_pred,
            "new_prediction": new_pred,
            "old_confidence": round(old_conf, 4),
            "new_confidence": round(new_conf, 4),
            "changed_yes_no": changed,
            "is_ood": "yes" if is_ood else "no",
            "ood_reasons": f"{'N_high ' if is_ood_n else ''}{'K_high' if is_ood_k else ''}".strip()
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"\nSaved comparison CSV to: {OUT_CSV}")

    print("\n--- Summary of Shadow Test ---")
    print(f"Districts tested: {len(out_df)}")
    print(f"Recommendations changed: {n_changed} / {len(out_df)} ({n_changed / len(out_df) * 100:.1f}%)")
    print(f"Districts with OOD N or K: {n_ood} / {len(out_df)} ({n_ood / len(out_df) * 100:.1f}%)")

    print("\nDetailed Comparison Table:")
    cols_display = ["district", "old_N", "old_P", "old_K", "new_N", "new_P", "new_K", "old_prediction", "new_prediction", "old_confidence", "new_confidence", "changed_yes_no"]
    print(out_df[cols_display].to_string(index=False))

    print("\nChanged Districts Breakdown:")
    changed_df = out_df[out_df["changed_yes_no"] == "yes"]
    for _, r in changed_df.iterrows():
        print(f"  {r['district']:16}: {r['old_prediction']} ({r['old_confidence']*100:.1f}%) -> {r['new_prediction']} ({r['new_confidence']*100:.1f}%) | N:{r['old_N']}->{r['new_N']}, P:{r['old_P']}->{r['new_P']}, K:{r['old_K']}->{r['new_K']}")

if __name__ == "__main__":
    run_shadow_test()
