import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.predict_api import predict_crop

async def main():
    test_image_path = os.path.join("cnn", "dataset", "test", "red", "test_red_000.jpg")
    with open(test_image_path, "rb") as f:
        img_bytes = f.read()

    # Test Bengaluru coordinates
    lat, lon = 12.9716, 77.5946
    print(f"--- Testing predict_crop for Bengaluru ({lat}, {lon}) ---")
    res = await predict_crop(img_bytes, lat, lon)
    print("Result:")
    for k, v in res.items():
        if k != "crops":
            print(f"  {k}: {v}")
    print("  Top crops:")
    for c in res["crops"]:
        print(f"    - {c['name']} ({c['confidence'] * 100:.1f}%) | Yield: {c.get('yield')} | Season: {c.get('season')}")

    # Test Dharwad coordinates with black soil image
    black_image_path = os.path.join("cnn", "dataset", "test", "black", "test_black_000.jpg")
    with open(black_image_path, "rb") as f:
        black_bytes = f.read()
    lat, lon = 15.4589, 75.0078
    print(f"\n--- Testing predict_crop for Dharwad ({lat}, {lon}) ---")
    res = await predict_crop(black_bytes, lat, lon)
    print("Result:")
    for k, v in res.items():
        if k != "crops":
            print(f"  {k}: {v}")
    print("  Top crops:")
    for c in res["crops"]:
        print(f"    - {c['name']} ({c['confidence'] * 100:.1f}%) | Yield: {c.get('yield')} | Season: {c.get('season')}")

if __name__ == "__main__":
    asyncio.run(main())
