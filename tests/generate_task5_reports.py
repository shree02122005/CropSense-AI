import os, sys, json
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["MPLCONFIGDIR"] = os.path.join(ROOT_DIR, ".cache", "matplotlib")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
sys.path.insert(0, ROOT_DIR)

from backend.predict_api import (
    predict_soil_from_bytes, _validate_soil_image, _weather_fallback,
    _soil_fallback, get_nearest_npk, detect_out_of_distribution_features,
    _soil_type_to_encoded, _predict_crops, crop_info, EXCLUDED_CLASSES
)

def run_predict(image_bytes: bytes, latitude: float, longitude: float, include_fruits: bool = False) -> dict:
    soil_type, soil_conf = predict_soil_from_bytes(image_bytes)
    if not _validate_soil_image(soil_type, soil_conf):
        raise ValueError(f"Invalid soil image: {soil_type} ({soil_conf:.1%})")
    
    temp, humidity, rainfall, location = _weather_fallback(latitude, longitude)
    ph_fb, soc_fb, is_fb, reason = _soil_fallback(latitude, longitude, reason="Offline demonstration")
    ph, organic_carbon = ph_fb, soc_fb
    raw_soil_nitrogen, converted_soil_nitrogen = None, None

    npk_info = get_nearest_npk(latitude, longitude)
    N = float(npk_info["N"])
    P = float(npk_info["P"])
    K = float(npk_info["K"])

    ood_info = detect_out_of_distribution_features(N, P, K, temp, humidity, ph, rainfall)
    soil_type_encoded = _soil_type_to_encoded(soil_type)

    top_crops = _predict_crops(
        N, P, K, temp, humidity, ph, rainfall,
        soil_type_encoded, latitude, longitude,
        include_fruits=include_fruits
    )

    crops = []
    for name, confidence, *_ in top_crops:
        info = crop_info(name)
        crops.append({
            "name":       name.title(),
            "confidence": round(confidence, 3),
            **info,
        })

    return {
        "location":                  location,
        "soil_type":                 soil_type.title(),
        "soil_type_encoded":         soil_type_encoded,
        "soil_confidence":           round(soil_conf, 3),
        "temperature":               round(temp, 1),
        "humidity":                  round(humidity, 1),
        "rainfall":                  round(rainfall, 1),
        "ph":                        round(ph, 2),
        "ph_is_fallback":            is_fb,
        "ph_source":                 reason,
        "organic_carbon":            round(organic_carbon, 2),
        "soilgrids_nitrogen_raw":    raw_soil_nitrogen,
        "soilgrids_nitrogen_gkg":    converted_soil_nitrogen,
        "N":                         round(N, 1),
        "P":                         round(P, 1),
        "K":                         round(K, 1),
        "npk_district":              npk_info.get("district"),
        "npk_reference_place":       npk_info.get("reference_place"),
        "npk_distance_km":           round(float(npk_info.get("distance_km", 0.0)), 2),
        "npk_source_type":           npk_info.get("source_type"),
        "npk_source_note":           npk_info.get("source_note"),
        "npk_out_of_training_range": ood_info["npk_out_of_training_range"],
        "npk_ood_features":          ood_info["npk_ood_features"],
        "all_ood_features":          ood_info["all_ood_features"],
        "ood_warning":               ood_info["ood_warning"],
        "training_ranges":           ood_info["training_ranges"],
        "feature_vector":            [round(N, 1), round(P, 1), round(K, 1), round(temp, 1), round(humidity, 1), round(ph, 2), round(rainfall, 1), soil_type_encoded],
        "crops":                     crops,
    }


def main():
    img_path = os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_000.jpg")
    print(f"Reading soil test image: {img_path}")
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    locations = [
        ("Bengaluru Urban", 12.9716, 77.5946),
        ("Mysuru", 12.2958, 76.6394),
        ("Belagavi", 15.8497, 74.4977),
    ]

    all_results = {}

    for loc_name, lat, lon in locations:
        print("\n" + "=" * 90)
        print(f"LOCATION: {loc_name} ({lat}, {lon})")
        print("=" * 90)

        # 1. False
        res_false = run_predict(img_bytes, lat, lon, include_fruits=False)
        print(f"\n--- [1] {loc_name} (include_fruits=false: FIELD CROPS ONLY) ---")
        print(json.dumps(res_false, indent=2))

        # 2. True
        res_true = run_predict(img_bytes, lat, lon, include_fruits=True)
        print(f"\n--- [2] {loc_name} (include_fruits=true: UNFILTERED ORIGINAL) ---")
        print(json.dumps(res_true, indent=2))

        # Assertions
        assert res_false["npk_out_of_training_range"] is True, f"Expected OOD True for {loc_name}"
        assert res_false["ood_warning"] is not None, f"Expected ood_warning for {loc_name}"
        crops_f = [c["name"].lower() for c in res_false["crops"]]
        crops_t = [c["name"].lower() for c in res_true["crops"]]
        assert not any(c in EXCLUDED_CLASSES for c in crops_f), f"Fruit leaked: {crops_f}"

        print(f"\n[Check] {loc_name}:")
        print(f"  OOD: {res_false['npk_out_of_training_range']} (Features: {res_false['npk_ood_features']})")
        print(f"  Field crops (false): {crops_f}")
        print(f"  Unfiltered crops (true): {crops_t}")

        all_results[loc_name] = {
            "include_fruits_false": res_false,
            "include_fruits_true": res_true,
        }

    out_file = os.path.join(ROOT_DIR, "tests", "results", "task5_predictions_3locations.json")
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nAll 3 locations successfully verified and saved to {out_file}")


if __name__ == "__main__":
    main()
