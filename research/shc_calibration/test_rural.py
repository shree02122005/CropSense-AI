import httpx
import json
import time

def test_rural():
    # Mandya centroid: 12.524, 76.896
    lat, lon = 12.524, 76.896
    
    # Test 1: all 6 properties at 0-5cm
    props = ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'cec']
    q = '&'.join([f'property={p}' for p in props] + ['depth=0-5cm', 'value=mean'])
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&{q}"
    print("Testing URL:", url)
    t0 = time.time()
    try:
        r = httpx.get(url, timeout=20, headers={'User-Agent': 'CropSense-Research/1.0'})
        print(f"Status: {r.status_code} in {time.time()-t0:.2f}s")
        if r.status_code == 200:
            d = r.json()
            layers = d.get('properties', {}).get('layers', [])
            print("Layers returned:", len(layers))
            for l in layers:
                name = l['name']
                fac = l['unit_measure']['d_factor']
                for dep in l['depths']:
                    val = dep['values'].get('mean')
                    print(f"  {name} {dep['label']}: val={val}, scaled={val/fac if val is not None else None}")
    except Exception as e:
        print("Failed:", e)

if __name__ == '__main__':
    test_rural()
