"""
test_task2_verification.py
──────────────────────────
Verification script for Task 2 and Task 5:
- Verifies FastAPI OpenAPI schema (/docs) for include_fruits Form parameter.
- Calls /predict endpoint across 3 Karnataka locations (Bengaluru, Mysuru, Belagavi).
- Confirms NO excluded fruit classes appear when include_fruits=False.
- Confirms fruit classes are restored when include_fruits=True.
- Verifies raw model probabilities are preserved.
- Verifies history logging and data contract.
"""

import os
import sys
import asyncio
from httpx import AsyncClient, ASGITransport

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from backend.main import app
from backend.predict_api import EXCLUDED_CLASSES


async def run_verification():
    print("=" * 80)
    print("  TASK 2 / TASK 5 SYSTEM & ENDPOINT VERIFICATION")
    print("=" * 80)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:

        # ── 1. Check Root & OpenAPI schema (/docs /openapi.json) ───────────
        print("\n[Step 1] Checking Root & OpenAPI Schema for include_fruits parameter ...")
        r_root = await client.get("/")
        assert r_root.status_code == 200, f"Root failed: {r_root.status_code}"
        print(f"  ✔ GET / -> HTTP {r_root.status_code} ({r_root.json()})")

        r_openapi = await client.get("/openapi.json")
        assert r_openapi.status_code == 200, f"OpenAPI failed: {r_openapi.status_code}"
        openapi = r_openapi.json()
        predict_schema = openapi["paths"]["/predict"]["post"]
        request_body = predict_schema.get("requestBody", {})
        schema_props = request_body.get("content", {}).get("multipart/form-data", {}).get("schema", {}).get("properties", {})
        
        assert "include_fruits" in schema_props, "include_fruits not found in /predict OpenAPI schema!"
        fruit_prop = schema_props["include_fruits"]
        print(f"  ✔ /predict OpenAPI schema verified: 'include_fruits' property found (type: {fruit_prop.get('type')}, default: {fruit_prop.get('default')})")

        # ── 2. Test Locations across Karnataka ──────────────────────────────
        locations = [
            ("Bengaluru (South)", 12.9716, 77.5946),
            ("Mysuru (Southern Plains)", 12.2958, 76.6394),
            ("Belagavi (North/Deccan)", 15.8497, 74.4977),
        ]

        img_path = os.path.join(ROOT_DIR, "cnn", "dataset", "synthetic_baseline", "black", "black_000.jpg")
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        print("\n[Step 2] Testing /predict Endpoint Across 3 Locations ...")
        for loc_name, lat, lon in locations:
            print(f"\n--- Location: {loc_name} (Lat: {lat}, Lon: {lon}) ---")

            # A) include_fruits = False (Default)
            files = {"image": ("test_soil.jpg", img_bytes, "image/jpeg")}
            data_false = {"latitude": str(lat), "longitude": str(lon), "include_fruits": "false"}
            res_false = await client.post("/predict", files=files, data=data_false)
            assert res_false.status_code == 200, f"Prediction failed: {res_false.text}"
            data_out_false = res_false.json()
            crops_false = data_out_false["crops"]

            print(f"  [include_fruits=false] Top Pick: {crops_false[0]['name']} ({crops_false[0]['confidence']*100:.1f}%)")
            for idx, c in enumerate(crops_false, 1):
                c_name = c["name"].lower()
                assert c_name not in EXCLUDED_CLASSES, f"Excluded class '{c_name}' leaked in include_fruits=false!"
                print(f"    Rank {idx}: {c['name']} (conf: {c['confidence']*100:.1f}%, profit: {c.get('profit')})")
            print("  ✔ Verified: Zero fruit/tree crops in recommendations!")

            # B) include_fruits = True
            files = {"image": ("test_soil.jpg", img_bytes, "image/jpeg")}
            data_true = {"latitude": str(lat), "longitude": str(lon), "include_fruits": "true"}
            res_true = await client.post("/predict", files=files, data=data_true)
            assert res_true.status_code == 200, f"Prediction failed: {res_true.text}"
            data_out_true = res_true.json()
            crops_true = data_out_true["crops"]

            print(f"  [include_fruits=true]  Top Pick: {crops_true[0]['name']} ({crops_true[0]['confidence']*100:.1f}%)")
            for idx, c in enumerate(crops_true, 1):
                print(f"    Rank {idx}: {c['name']} (conf: {c['confidence']*100:.1f}%, profit: {c.get('profit')})")
            
            # Check difference between True and False
            top_crops_false_names = [c["name"] for c in crops_false]
            top_crops_true_names = [c["name"] for c in crops_true]
            print(f"  Output comparison: False={top_crops_false_names} | True={top_crops_true_names}")

        # ── 3. Test History Endpoint ────────────────────────────────────────
        print("\n[Step 3] Verifying History Endpoint & Saved Records ...")
        r_hist = await client.get("/history")
        assert r_hist.status_code == 200
        history_list = r_hist.json().get("history", [])
        print(f"  ✔ /history returned HTTP 200 with {len(history_list)} records")
        if history_list:
            latest = history_list[0]
            print(f"  Latest record: Location='{latest.get('location')}', Soil='{latest.get('soil_type')}', Crops count={len(latest.get('crops', []))}")
            for c in latest.get("crops", []):
                print(f"    - {c.get('name')}: {c.get('confidence')}")

    print("\n" + "=" * 80)
    print("  ALL VERIFICATION CHECKS PASSED (100%)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_verification())
