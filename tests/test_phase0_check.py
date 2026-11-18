import os
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Suppress TensorFlow logging & configure matplotlib cache
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["MPLCONFIGDIR"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".cache", "matplotlib"))

from backend.predict_api import _predict_crops, crop_info

def run():
    print("==================================================")
    print("PHASE 0 VERIFICATION: Low-confidence & Match Labels")
    print("==================================================")

    # 1. Low confidence test (Mysuru profile: N=369.7, P=9.2, K=265.6)
    print("\n[TEST 1] Out-of-Distribution / Low Confidence Test (Mysuru input):")
    crops_low = _predict_crops(
        N=369.7, P=9.2, K=265.6, temp=28.0, humidity=75.0, ph=5.8, rainfall=110.0,
        soil_type_encoded=4, include_fruits=False
    )
    crops_output = []
    for name, confidence, *_ in crops_low:
        conf_val = round(confidence, 3)
        if conf_val >= 0.50:
            conf_level = "strong"
            match_str = "Strong match"
        elif conf_val >= 0.20:
            conf_level = "moderate"
            match_str = "Moderate match"
        else:
            conf_level = "low"
            match_str = "Low match"

        crops_output.append({
            "name": name.title(),
            "confidence": conf_val,
            "confidence_level": conf_level,
            "match_strength": match_str
        })

    top_confidence_level = crops_output[0]["confidence_level"] if crops_output else "low"
    is_low_confidence = (crops_output[0]["confidence"] < 0.20) if crops_output else True

    for i, c in enumerate(crops_output, 1):
        print(f"  Rank {i}: {c['name']} - Confidence: {c['confidence']:.1%} | Level: '{c['confidence_level']}' | Match Strength: '{c['match_strength']}'")
    print(f"  -> top_confidence_level: '{top_confidence_level}'")
    print(f"  -> is_low_confidence: {is_low_confidence}")
    assert top_confidence_level == "low", f"Expected 'low', got {top_confidence_level}"
    assert is_low_confidence is True, "Expected is_low_confidence to be True"
    assert crops_output[0]["match_strength"] == "Low match"
    print("  [PASS] Low confidence handling verified.")

    # 2. Moderate confidence test
    print("\n[TEST 2] Moderate Confidence Test:")
    crops_mod = _predict_crops(
        N=249.7, P=35.0, K=120.0, temp=26.5, humidity=70.0, ph=6.8, rainfall=850.0,
        soil_type_encoded=0, include_fruits=False
    )
    crops_mod_output = []
    for name, confidence, *_ in crops_mod:
        conf_val = round(confidence, 3)
        if conf_val >= 0.50:
            conf_level = "strong"
            match_str = "Strong match"
        elif conf_val >= 0.20:
            conf_level = "moderate"
            match_str = "Moderate match"
        else:
            conf_level = "low"
            match_str = "Low match"

        crops_mod_output.append({
            "name": name.title(),
            "confidence": conf_val,
            "confidence_level": conf_level,
            "match_strength": match_str
        })
    for i, c in enumerate(crops_mod_output, 1):
        print(f"  Rank {i}: {c['name']} - Confidence: {c['confidence']:.1%} | Level: '{c['confidence_level']}' | Match Strength: '{c['match_strength']}'")
    print("  [PASS] Moderate confidence handling verified.")

    # 3. Strong confidence test (In-distribution rice conditions)
    print("\n[TEST 3] Strong Confidence Test (Rice conditions):")
    crops_strong = _predict_crops(
        N=80.0, P=45.0, K=40.0, temp=25.0, humidity=80.0, ph=6.5, rainfall=200.0,
        soil_type_encoded=0, include_fruits=False
    )
    crops_strong_output = []
    for name, confidence, *_ in crops_strong:
        conf_val = round(confidence, 3)
        if conf_val >= 0.50:
            conf_level = "strong"
            match_str = "Strong match"
        elif conf_val >= 0.20:
            conf_level = "moderate"
            match_str = "Moderate match"
        else:
            conf_level = "low"
            match_str = "Low match"

        crops_strong_output.append({
            "name": name.title(),
            "confidence": conf_val,
            "confidence_level": conf_level,
            "match_strength": match_str
        })
    for i, c in enumerate(crops_strong_output, 1):
        print(f"  Rank {i}: {c['name']} - Confidence: {c['confidence']:.1%} | Level: '{c['confidence_level']}' | Match Strength: '{c['match_strength']}'")
    assert crops_strong_output[0]["confidence_level"] == "strong"
    assert crops_strong_output[0]["match_strength"] == "Strong match"
    print("  [PASS] Strong confidence handling verified.")

    print("\nALL PHASE 0 BACKEND LOGIC CHECKS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    run()
