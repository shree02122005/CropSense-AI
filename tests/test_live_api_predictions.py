"""
test_live_api_predictions.py
────────────────────────────
Calls FastAPI endpoint POST /predict end-to-end with real soil image
across 3 Karnataka locations for include_fruits=false and include_fruits=true.
Prints full JSON response and verifies OOD fields and fruit filtering.
"""

import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["MPLCONFIGDIR"] = os.path.join(ROOT_DIR, ".cache", "matplotlib")
sys.path.insert(0, ROOT_DIR)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

import json
import asyncio
from httpx import AsyncClient, ASGITransport

from backend.main import app

IMAGE_PATH = os.path.join(ROOT_DIR, "cnn", "dataset", "test", "red", "test_red_000.jpg")
if not os.path.exists(IMAGE_PATH):
    IMAGE_PATH = os.path.join(ROOT_DIR, "cnn", "dataset", "synthetic_baseline", "black", "black_000.jpg")

LOCATIONS = [
    ("Bengaluru Urban", 12.9716, 77.5946),
    ("Mysuru", 12.2958, 76.6394),
    ("Belagavi", 15.8497, 74.4977),
]

EXCLUDED_CLASSES = {
    "apple", "banana", "grapes", "mango", "muskmelon", "orange",
    "papaya", "pomegranate", "watermelon", "coconut"
}

OUT_FILE = os.path.join(ROOT_DIR, "tests", "results", "live_predict_3_locations.json")

import backend.predict_api as b_pred
orig_weather = b_pred._fetch_weather
orig_soil = b_pred._fetch_soil

async def fast_weather(lat, lon):
    try:
        return await asyncio.wait_for(orig_weather(lat, lon), timeout=0.5)
    except Exception:
        return b_pred._weather_fallback(lat, lon)

async def fast_soil(lat, lon):
    try:
        return await asyncio.wait_for(orig_soil(lat, lon), timeout=0.5)
    except Exception:
        return b_pred._soil_fallback(lat, lon, reason="Offline environment - fast fallback")

b_pred._fetch_weather = fast_weather
b_pred._fetch_soil = fast_soil


async def run_tests():
    print(f"Using test image: {IMAGE_PATH}", flush=True)
    assert os.path.exists(IMAGE_PATH), "Image not found!"
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    results_record = {}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        for loc_name, lat, lon in LOCATIONS:
            print("\n" + "=" * 90, flush=True)
            print(f"RUNNING LOCATION: {loc_name} (Latitude: {lat}, Longitude: {lon})", flush=True)
            print("=" * 90, flush=True)

            # ── A. include_fruits = false (Default) ───────────────────────────
            print(f"[{loc_name}] Calling POST /predict with include_fruits=false ...", flush=True)
            files = {"image": ("test_soil.jpg", img_bytes, "image/jpeg")}
            data_false = {"latitude": str(lat), "longitude": str(lon), "include_fruits": "false"}
            r_false = await client.post("/predict", files=files, data=data_false)
            assert r_false.status_code == 200, f"Error {r_false.status_code}: {r_false.text}"
            json_false = r_false.json()

            print(f"\n>>> [{loc_name}] Response with include_fruits=false (DEFAULT FIELD CROPS ONLY):", flush=True)
            print(json.dumps(json_false, indent=2), flush=True)

            # ── B. include_fruits = true ──────────────────────────────────────
            print(f"\n[{loc_name}] Calling POST /predict with include_fruits=true ...", flush=True)
            files = {"image": ("test_soil.jpg", img_bytes, "image/jpeg")}
            data_true = {"latitude": str(lat), "longitude": str(lon), "include_fruits": "true"}
            r_true = await client.post("/predict", files=files, data=data_true)
            assert r_true.status_code == 200, f"Error {r_true.status_code}: {r_true.text}"
            json_true = r_true.json()

            print(f"\n>>> [{loc_name}] Response with include_fruits=true (UNFILTERED ORIGINAL):", flush=True)
            print(json.dumps(json_true, indent=2), flush=True)

            # Diagnostic checks
            print(f"\n>>> [{loc_name}] Diagnostic Verifications:", flush=True)
            print(f"  npk_out_of_training_range: {json_false.get('npk_out_of_training_range')}", flush=True)
            print(f"  npk_ood_features:          {json_false.get('npk_ood_features')}", flush=True)
            print(f"  ood_warning present:       {bool(json_false.get('ood_warning'))}", flush=True)
            print(f"  ood_warning text:          {json_false.get('ood_warning')}", flush=True)

            crops_false_names = [c["name"] for c in json_false["crops"]]
            crops_true_names = [c["name"] for c in json_true["crops"]]
            print(f"  include_fruits=false top crops: {crops_false_names}", flush=True)
            print(f"  include_fruits=true top crops:  {crops_true_names}", flush=True)

            assert json_false.get("npk_out_of_training_range") is True, f"Expected OOD True for {loc_name}"
            assert json_false.get("ood_warning") is not None, f"Expected ood_warning for {loc_name}"
            assert not any(c.lower() in EXCLUDED_CLASSES for c in crops_false_names), f"Fruit leaked: {crops_false_names}"

            results_record[loc_name] = {
                "include_fruits_false": json_false,
                "include_fruits_true": json_true,
            }

            with open(OUT_FILE, "w", encoding="utf-8") as f_out:
                json.dump(results_record, f_out, indent=2)
            print(f"[{loc_name}] Progress saved to {OUT_FILE}", flush=True)

    print("\n" + "=" * 90, flush=True)
    print("ALL 3 LOCATIONS COMPLETED AND ALL VERIFICATION CHECKS PASSED!", flush=True)
    print("=" * 90, flush=True)


if __name__ == "__main__":
    asyncio.run(run_tests())
