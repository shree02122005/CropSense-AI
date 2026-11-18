import os, sys

# ── Step 0: Pre-configure environment before any ML/visual libraries load ────
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["MPLCONFIGDIR"] = os.path.join(ROOT_DIR, ".cache", "matplotlib")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["PYTHONUNBUFFERED"] = "1"
sys.path.insert(0, ROOT_DIR)

import json
import asyncio
from httpx import AsyncClient, ASGITransport

import backend.predict_api as b_pred
from backend.main import app

# Wrap _fetch_weather and _fetch_soil with fast-fallback in offline sandbox
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
        return b_pred._soil_fallback(lat, lon, reason="Sandbox offline - fast fallback")

b_pred._fetch_weather = fast_weather
b_pred._fetch_soil = fast_soil

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

OUT_FILE = os.path.join(ROOT_DIR, "tests", "results", "task5_predictions_3locations.json")


async def main():
    print(f"Loading real test image: {IMAGE_PATH}", flush=True)
    assert os.path.exists(IMAGE_PATH), "Image not found!"
    with open(IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    results = {}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        for loc_name, lat, lon in LOCATIONS:
            print("\n" + "=" * 90, flush=True)
            print(f"LOCATION: {loc_name} (Latitude: {lat}, Longitude: {lon})", flush=True)
            print("=" * 90, flush=True)

            # ── 1. POST /predict with include_fruits=false (Default) ──────────
            print(f"\n--- [1] {loc_name}: POST /predict (include_fruits=false) ---", flush=True)
            files = {"image": ("test_soil.jpg", img_bytes, "image/jpeg")}
            data_false = {"latitude": str(lat), "longitude": str(lon), "include_fruits": "false"}
            r_false = await client.post("/predict", files=files, data=data_false)
            assert r_false.status_code == 200, f"Error {r_false.status_code}: {r_false.text}"
            res_false = r_false.json()

            print(json.dumps(res_false, indent=2), flush=True)

            # ── 2. POST /predict with include_fruits=true ─────────────────────
            print(f"\n--- [2] {loc_name}: POST /predict (include_fruits=true) ---", flush=True)
            files = {"image": ("test_soil.jpg", img_bytes, "image/jpeg")}
            data_true = {"latitude": str(lat), "longitude": str(lon), "include_fruits": "true"}
            r_true = await client.post("/predict", files=files, data=data_true)
            assert r_true.status_code == 200, f"Error {r_true.status_code}: {r_true.text}"
            res_true = r_true.json()

            print(json.dumps(res_true, indent=2), flush=True)

            # ── Verifications ─────────────────────────────────────────────────
            print(f"\n--- Diagnostics & Assertions for {loc_name} ---", flush=True)
            print(f"  npk_out_of_training_range: {res_false.get('npk_out_of_training_range')}", flush=True)
            print(f"  npk_ood_features:          {res_false.get('npk_ood_features')}", flush=True)
            print(f"  ood_warning present:       {bool(res_false.get('ood_warning'))}", flush=True)
            print(f"  ood_warning text:          {res_false.get('ood_warning')}", flush=True)

            crops_false = [c["name"] for c in res_false["crops"]]
            crops_true = [c["name"] for c in res_true["crops"]]
            print(f"  include_fruits=false crops: {crops_false}", flush=True)
            print(f"  include_fruits=true crops:  {crops_true}", flush=True)

            assert res_false.get("npk_out_of_training_range") is True, f"Expected OOD True for {loc_name}"
            assert res_false.get("ood_warning") is not None, f"Expected ood_warning for {loc_name}"
            assert not any(c.lower() in EXCLUDED_CLASSES for c in crops_false), f"Fruit leaked: {crops_false}"

            results[loc_name] = {
                "include_fruits_false": res_false,
                "include_fruits_true": res_true,
            }

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll 3 locations successfully verified and saved to {OUT_FILE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
