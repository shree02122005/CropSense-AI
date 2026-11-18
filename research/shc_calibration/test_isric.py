import urllib.request
import urllib.parse
import json

def test_soilgrids():
    lat, lon = 12.97, 77.59
    props = ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'cec']
    depths = ['0-5cm', '0-30cm']
    q = '&'.join([f'property={p}' for p in props] + [f'depth={d}' for d in depths] + ['value=mean'])
    url = f'https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&{q}'
    headers = {'User-Agent': 'CropSense-AI-Research/1.0'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            print("Status: SUCCESS!")
            print("Layers returned:", [l['name'] for l in data['properties']['layers']])
            for l in data['properties']['layers']:
                fac = l['unit_measure']['d_factor']
                for d in l['depths']:
                    val = d['values'].get('mean')
                    print(f"  {l['name']} {d['label']}: raw={val}, scaled={val/fac if val is not None else None}")
    except Exception as e:
        print("Status: FAILED:", e)

if __name__ == "__main__":
    test_soilgrids()
