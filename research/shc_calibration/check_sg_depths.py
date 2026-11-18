import urllib.request
import json
import time

def check():
    props = ['nitrogen','phh2o','soc','clay','sand','cec']
    depths = ['0-5cm','0-30cm']
    q = '&'.join([f'property={p}' for p in props] + [f'depth={d}' for d in depths] + ['value=mean'])
    url = f'https://rest.isric.org/soilgrids/v2.0/properties/query?lat=12.97&lon=77.59&{q}'
    print("Querying:", url)
    req = urllib.request.Request(url, headers={'User-Agent': 'CropSense-AI-Research/1.0'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.load(r)
            print(f"Success in {time.time()-t0:.2f}s!")
            for l in d['properties']['layers']:
                print(l['name'], [f"{dep['label']}: {dep['values']['mean']}" for dep in l['depths']])
    except Exception as e:
        print(f"Failed in {time.time()-t0:.2f}s: {e}")

if __name__ == '__main__':
    check()
