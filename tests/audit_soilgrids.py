import httpx
import json

locations = [
    ("Bengaluru", 12.9716, 77.5946),
    ("Mysuru", 12.2958, 76.6394),
    ("Hassan", 13.0068, 76.1004),
    ("Kodagu", 12.4244, 75.7382),
    ("Belagavi", 15.8497, 74.4977),
    ("Kalaburagi", 17.3297, 76.8343),
]

for name, lat, lon in locations:
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=phh2o&property=soc&depth=0-5cm&value=mean"
    print(f"\nTesting {name} ({lat}, {lon})")
    print(f"URL: {url}")
    try:
        r = httpx.get(url, timeout=12)
        print(f"  HTTP Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            layers = d.get("properties", {}).get("layers", [])
            print(f"  Layers found: {[l.get('name') for l in layers]}")
            for l in layers:
                name_l = l.get("name")
                depths = l.get("depths", [])
                print(f"    Layer '{name_l}': {len(depths)} depths -> {depths}")
        else:
            print(f"  Non-200: {r.text[:200]}")
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}")
