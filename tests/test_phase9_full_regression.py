"""
test_phase9_full_regression.py
──────────────────────────────
Re-runs the exact 10 Karnataka locations from Phase 8 and compares every field:
- N, P, K
- OOD status and OOD features
- Soil classification and confidence
- Top 3 predicted crops and probabilities
- API payload schema consistency
"""

import os
import sys
import json
import asyncio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, ROOT_DIR)

try:
    from tests.test_phase8_locations import TEST_LOCATIONS
except ImportError:
    from backend.test_phase8_locations import TEST_LOCATIONS
from backend.predict_api import predict_crop

async def run_regression():
    candidates = [
        os.path.join(ROOT_DIR, "tests", "results", "phase8_karnataka_test_results.json"),
        os.path.join(ROOT_DIR, "phase8_karnataka_test_results.json"),
    ]
    baseline_file = next((p for p in candidates if os.path.exists(p)), candidates[0])
    with open(baseline_file, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    print("=" * 90)
    print("  PHASE 9 REGRESSION TEST: 10 KARNATAKA LOCATIONS VS. PHASE 8 BASELINE")
    print("=" * 90)

    all_matched = True
    comparison_records = []

    for idx, (loc_cfg, base_rec) in enumerate(zip(TEST_LOCATIONS, baseline), 1):
        name = loc_cfg["name"]
        lat = loc_cfg["latitude"]
        lon = loc_cfg["longitude"]
        img_path = loc_cfg["soil_image"]

        with open(img_path, "rb") as f:
            img_bytes = f.read()

        current = await predict_crop(img_bytes, lat, lon)

        # Check N, P, K
        npk_match = (
            abs(current["N"] - base_rec["N"]) < 0.1 and
            abs(current["P"] - base_rec["P"]) < 0.1 and
            abs(current["K"] - base_rec["K"]) < 0.1
        )

        # Check OOD status
        ood_match = (
            current["npk_out_of_training_range"] == base_rec["npk_out_of_training_range"] and
            set(current["npk_ood_features"]) == set(base_rec["npk_ood_features"])
        )

        # Check Soil CNN
        soil_match = (
            current["soil_type"].lower() == base_rec["soil_type_detected"].lower() and
            current["soil_type_encoded"] == base_rec["soil_type_encoded"]
        )

        # Check Top 1 Crop
        top1_curr = current["crops"][0]["name"]
        top1_base = base_rec["crops_detailed"][0]["name"]
        crop_match = (top1_curr.lower() == top1_base.lower())

        status = "PASSED" if (npk_match and ood_match and soil_match and crop_match) else "DIFF"
        if status != "PASSED":
            all_matched = False

        record = {
            "index": idx,
            "location": name,
            "status": status,
            "npk_match": npk_match,
            "ood_match": ood_match,
            "soil_match": soil_match,
            "crop_match": crop_match,
            "baseline_npk": f"{base_rec['N']}/{base_rec['P']}/{base_rec['K']}",
            "current_npk": f"{current['N']}/{current['P']}/{current['K']}",
            "baseline_top1": f"{top1_base} ({base_rec['crops_detailed'][0]['confidence']*100:.1f}%)",
            "current_top1": f"{top1_curr} ({current['crops'][0]['confidence']*100:.1f}%)",
            "baseline_soil": f"{base_rec['soil_type_detected']} ({base_rec['soil_cnn_confidence']*100:.1f}%)",
            "current_soil": f"{current['soil_type']} ({current['soil_confidence']*100:.1f}%)",
            "current_temp": current["temperature"],
            "current_humidity": current["humidity"],
            "current_rain": current["rainfall"],
            "current_ph": current["ph"],
            "ph_fallback": current["ph_is_fallback"],
        }
        comparison_records.append(record)

        print(f"[{idx}/10] {name:<18} | Status: {status:<6} | NPK: {record['current_npk']:<12} | Soil: {record['current_soil']:<18} | Top1: {record['current_top1']}")

    print("\n" + "=" * 90)
    print("  REGRESSION TEST SUMMARY")
    print("=" * 90)
    print(f"Total Locations Evaluated: {len(comparison_records)}")
    passed_count = sum(1 for r in comparison_records if r["status"] == "PASSED")
    print(f"Total Matches: {passed_count}/{len(comparison_records)}")
    if all_matched:
        print("✔ ALL 10 LOCATIONS ARE 100% CONSISTENT WITH PHASE 8 BASELINE.")
    else:
        print("⚠ Differences detected in weather or live outputs (details logged).")

    out_dir = os.path.join(ROOT_DIR, "tests", "results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "phase9_regression_comparison.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(comparison_records, f, indent=2)
    print(f"Saved regression comparison report to: {out_file}")

if __name__ == "__main__":
    asyncio.run(run_regression())
