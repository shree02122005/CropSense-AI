import urllib.request
import json
import time

def test_full():
    lat, lon = 12.97, 77.59
    props = ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'cec']
    depths = ['0-5cm', '5-15cm', '15-30cm']
    q = '&'.join([f'property={p}' for p in props] + [f'depth={d}' for d in depths] + ['value=mean'])
    url = f'https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&{q}'
    print("Testing URL:", url)
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CropSense-AI/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
            print(f"Success in {time.time()-t0:.2f}s!")
            for l in data['properties']['layers']:
                fac = l['unit_measure']['d_factor']
                print(l['name'], {d['label']: d['values']['mean']/fac if d['values']['mean'] is not None else None for d in l['depths']})
    except Exception as e:
        print("Failed:", e)

if __name__ == '__main__':
    test_full()
