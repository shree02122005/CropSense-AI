"""
test_phase7_locations.py
────────────────────────
Phase 7 Validation: Tests backend prediction pipeline across 10 Karnataka locations:
1. Bengaluru
2. Mysuru
3. Hassan
4. Kodagu/Madikeri
5. Shivamogga
6. Mangaluru
7. Belagavi
8. Dharwad
9. Raichur
10. Kalaburagi

For each location, verifies:
- Dynamic N, P, K from legitimate Karnataka reference dataset
- OpenWeather API weather data
- SoilGrids pH & organic carbon + ph_is_fallback transparency
- Soil CNN inference
- Pure Random Forest prediction (NO multipliers, NO clipping)
- Out-of-distribution (OOD) detection
- Exact 8-feature order: [N, P, K, temp, humidity, ph, rainfall, soil_type_encoded]
"""
import os
import sys
import asyncio
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, ROOT_DIR)

from backend.predict_api import predict_crop, _load_ml_model, _verify_ml_model_features

TEST_LOCATIONS = [
    {
        "name": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_000.jpg")
    },
    {
        "name": "Mysuru",
        "latitude": 12.2958,
        "longitude": 76.6394,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_001.jpg")
    },
    {
        "name": "Hassan",
        "latitude": 13.0068,
        "longitude": 76.1004,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_002.jpg")
    },
    {
        "name": "Kodagu/Madikeri",
        "latitude": 12.4244,
        "longitude": 75.7382,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "loamy", "test_loamy_000.jpg")
    },
    {
        "name": "Shivamogga",
        "latitude": 13.9299,
        "longitude": 75.5681,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "loamy", "test_loamy_001.jpg")
    },
    {
        "name": "Mangaluru",
        "latitude": 12.9141,
        "longitude": 74.8560,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "sandy", "test_sandy_000.jpg")
    },
    {
        "name": "Belagavi",
        "latitude": 15.8497,
        "longitude": 74.4977,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_000.jpg")
    },
    {
        "name": "Dharwad",
        "latitude": 15.4589,
        "longitude": 75.0078,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_001.jpg")
    },
    {
        "name": "Raichur",
        "latitude": 16.2120,
        "longitude": 77.3439,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_002.jpg")
    },
    {
        "name": "Kalaburagi",
        "latitude": 17.3297,
        "longitude": 76.8343,
        "soil_image": os.path.join(ROOT_DIR, "cnn", "dataset", "test", "black", "test_black_003.jpg")
    }
]


async def run_tests():
    print("=" * 85)
    print("  PHASE 7: BACKEND PREDICTION PIPELINE VERIFICATION (10 KARNATAKA LOCATIONS)")
    print("=" * 85)

    # 1. Verify ML Model Loading
    print("\n[Step 1] Verifying Random Forest model loading ...")
    model = _load_ml_model()
    _verify_ml_model_features(model)
    print(f"  ✔ Model loaded successfully: {type(model).__name__}")
    print(f"  ✔ Model expects {model.n_features_in_} features")
    print(f"  ✔ Total classes ({len(model.classes_)}): {list(model.classes_)}")

    results = []

    print("\n[Step 2] Executing predictions for 10 Karnataka locations ...\n")
    for idx, loc in enumerate(TEST_LOCATIONS, 1):
        name = loc["name"]
        lat = loc["latitude"]
        lon = loc["longitude"]
        img_path = loc["soil_image"]

        assert os.path.exists(img_path), f"Soil image not found: {img_path}"
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        print(f"-------------------------------------------------------------------------------------")
        print(f"[{idx}/10] Testing Location: {name} ({lat:.4f}°N, {lon:.4f}°E)")
        print(f"        Soil input image: {os.path.basename(img_path)}")

        res = await predict_crop(img_bytes, lat, lon)

        top_crops_summary = [f"{c['name']} ({c['confidence']*100:.1f}%)" for c in res["crops"]]
        
        record = {
            "location_tested": name,
            "resolved_location": res.get("location"),
            "latitude": lat,
            "longitude": lon,
            "N": res["N"],
            "P": res["P"],
            "K": res["K"],
            "npk_out_of_training_range": res.get("npk_out_of_training_range"),
            "npk_ood_features": res.get("npk_ood_features"),
            "all_ood_features": res.get("all_ood_features"),
            "ood_warning": res.get("ood_warning"),
            "npk_district": res.get("npk_district"),
            "npk_reference_place": res.get("npk_reference_place"),
            "npk_source_type": res.get("npk_source_type"),
            "npk_distance_km": res.get("npk_distance_km"),
            "temperature": res["temperature"],
            "humidity": res["humidity"],
            "rainfall": res["rainfall"],
            "ph": res["ph"],
            "ph_is_fallback": res.get("ph_is_fallback"),
            "ph_source": res.get("ph_source"),
            "organic_carbon": res["organic_carbon"],
            "soil_type": res["soil_type"],
            "soil_type_encoded": res["soil_type_encoded"],
            "soil_confidence": res["soil_confidence"],
            "feature_vector": res["feature_vector"],
            "top_crops": top_crops_summary,
            "crops_detailed": res["crops"],
            "training_ranges": res.get("training_ranges")
        }
        results.append(record)

        ood_str = f"OOD={res.get('npk_out_of_training_range')} ({res.get('npk_ood_features')})"
        print(f"        ✔ N/P/K (raw):   N={res['N']}, P={res['P']}, K={res['K']} (kg/ha) [{res.get('npk_district')}, {res.get('npk_source_type')}] -> {ood_str}")
        print(f"        ✔ Weather:       Temp={res['temperature']}°C, Humidity={res['humidity']}%, Rain={res['rainfall']}mm (Location: {res.get('location')})")
        print(f"        ✔ Soil/pH:       pH={res['ph']} (fallback={res.get('ph_is_fallback')}), SOC={res['organic_carbon']}% [{res.get('ph_source')}]")
        print(f"        ✔ Soil CNN:      Type={res['soil_type']} (encoded={res['soil_type_encoded']}), Conf={res['soil_confidence']*100:.1f}%")
        print(f"        ✔ Feature Vector:{res['feature_vector']}")
        print(f"        ✔ Top 3 Crops:   {', '.join(top_crops_summary)}")

    # Summary table
    print("\n" + "=" * 90)
    print("  PHASE 7 SUMMARY TEST MATRIX (10 LOCATIONS)")
    print("=" * 90)
    header = f"{'Location':16} | {'N/P/K':14} | {'OOD?':5} | {'OOD Feat':10} | {'Temp':5} | {'Hum':4} | {'Rain':5} | {'pH':5} | {'pH FB?':7} | {'Soil Type':8} | {'Top 1 Crop':15}"
    print(header)
    print("-" * len(header))
    for r in results:
        npk_s = f"{r['N']:.0f}/{r['P']:.0f}/{r['K']:.0f}"
        top1 = r["top_crops"][0] if r["top_crops"] else "None"
        ood_f = ",".join(r["npk_ood_features"]) if r["npk_ood_features"] else "None"
        fb_s = "YES" if r["ph_is_fallback"] else "NO"
        print(f"{r['location_tested']:16} | {npk_s:14} | {str(r['npk_out_of_training_range']):5} | {ood_f:10} | {r['temperature']:4.1f}C | {r['humidity']:3.0f}% | {r['rainfall']:4.1f} | {r['ph']:5.2f} | {fb_s:7} | {r['soil_type']:8} | {top1}")

    # Save detailed JSON results for documentation
    out_file = os.path.join(ROOT_DIR, "phase7_backend_test_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved full Phase 7 test results to: {out_file}")

    # Verification assertions
    print("\n[Step 3] Automated Verification Assertions:")
    all_npks = [(r["N"], r["P"], r["K"]) for r in results]
    assert (90, 40, 40) not in all_npks, "Found hardcoded N=90, P=40, K=40!"
    print("  ✔ Assertion 1: Hardcoded N=90, P=40, K=40 is completely eliminated.")

    # Check that raw values are NOT clipped
    has_unclipped_high_k = any(r["K"] > 236.77 for r in results)
    has_unclipped_high_n = any(r["N"] > 153.79 for r in results)
    assert has_unclipped_high_k and has_unclipped_high_n, "N/P/K values appear to be clipped!"
    print("  ✔ Assertion 2: Raw published N/P/K values are passed directly WITHOUT clipping or scaling.")

    # Check 8-feature vector structure
    for r in results:
        fv = r["feature_vector"]
        assert len(fv) == 8, f"Feature vector length is {len(fv)}, expected 8!"
        assert fv[0] == r["N"] and fv[1] == r["P"] and fv[2] == r["K"], "NPK position mismatch in feature vector!"
        assert fv[7] == r["soil_type_encoded"], "Soil type position mismatch in feature vector!"
    print("  ✔ Assertion 3: Feature vector structure [N, P, K, temp, hum, ph, rain, soil_enc] strictly verified.")

    # Check OOD detection
    for r in results:
        assert "npk_out_of_training_range" in r, "Missing npk_out_of_training_range key!"
        assert "npk_ood_features" in r, "Missing npk_ood_features key!"
        if r["N"] > 153.79:
            assert "N" in r["npk_ood_features"], f"Failed to detect N OOD for {r['location_tested']}"
        if r["K"] > 236.77:
            assert "K" in r["npk_ood_features"], f"Failed to detect K OOD for {r['location_tested']}"
    print("  ✔ Assertion 4: Out-of-distribution detection correctly flags N and K across all locations.")

    print("\nPhase 7 test suite execution finished successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())
