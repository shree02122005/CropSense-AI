"""
test_live_predict_3_locations.py
────────────────────────────────
Calls the live FastAPI backend on http://127.0.0.1:8000/predict
for 3 distinct Karnataka locations with both include_fruits=False and include_fruits=True.
"""

import os
import requests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_PATH = os.path.join(ROOT_DIR, "cnn", "dataset", "synthetic_baseline", "black", "black_000.jpg")

EXCLUDED_CLASSES = {
    "apple", "banana", "grapes", "mango", "muskmelon", "orange",
    "papaya", "pomegranate", "watermelon", "coconut"
}

LOCATIONS = [
    ("Bengaluru Urban", 12.9716, 77.5946),
    ("Mysuru", 12.2958, 76.6394),
    ("Belagavi", 15.8497, 74.4977),
]

def test_live():
    print("=" * 80)
    print("LIVE BACKEND VERIFICATION: 3 LOCATIONS (HTTP POST /predict)")
    print("=" * 80)

    for loc_name, lat, lon in LOCATIONS:
        print(f"\n=======================================================")
        print(f"Testing Location: {loc_name} ({lat}, {lon})")
        print(f"=======================================================")

        # 1. include_fruits = False (Default)
        with open(IMAGE_PATH, "rb") as f:
            files = {"image": ("test_soil.jpg", f, "image/jpeg")}
            data = {"latitude": lat, "longitude": lon, "include_fruits": "false"}
            r_false = requests.post("http://127.0.0.1:8000/predict", files=files, data=data, timeout=30)
        
        assert r_false.status_code == 200, f"Error {r_false.status_code}: {r_false.text}"
        res_false = r_false.json()
        crops_false = res_false["crops"]
        
        print(f"[include_fruits=false] Top Pick: {crops_false[0]['name']} ({crops_false[0]['confidence']*100:.1f}%)")
        print(f"  All Top 3 Recommendations:")
        for i, c in enumerate(crops_false, 1):
            c_name = c["name"].lower()
            assert c_name not in EXCLUDED_CLASSES, f"LEAK! Excluded class '{c_name}' returned when include_fruits=False"
            print(f"    {i}. {c['name']} - Confidence: {c['confidence']*100:.1f}% | Profit: {c.get('profit')} | Season: {c.get('season')}")
        print("  ✔ Verified: Zero fruit/tree crops in display!")

        # 2. include_fruits = True
        with open(IMAGE_PATH, "rb") as f:
            files = {"image": ("test_soil.jpg", f, "image/jpeg")}
            data = {"latitude": lat, "longitude": lon, "include_fruits": "true"}
            r_true = requests.post("http://127.0.0.1:8000/predict", files=files, data=data, timeout=30)
        
        assert r_true.status_code == 200, f"Error {r_true.status_code}: {r_true.text}"
        res_true = r_true.json()
        crops_true = res_true["crops"]
        
        print(f"\n[include_fruits=true]  Top Pick: {crops_true[0]['name']} ({crops_true[0]['confidence']*100:.1f}%)")
        print(f"  All Top 3 Recommendations:")
        for i, c in enumerate(crops_true, 1):
            print(f"    {i}. {c['name']} - Confidence: {c['confidence']*100:.1f}% | Profit: {c.get('profit')} | Season: {c.get('season')}")

        has_fruit = any(c["name"].lower() in EXCLUDED_CLASSES for c in crops_true)
        print(f"  Fruit crop present in unfiltered original output: {'YES' if has_fruit else 'NO'}")
        print(f"  Filter effect summary: {crops_true[0]['name']} -> {crops_false[0]['name']}")

    print("\n" + "=" * 80)
    print("LIVE ENDPOINT VERIFICATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_live()
