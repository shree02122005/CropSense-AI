import urllib.request
import json
import time

props = ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'cec']
lat, lon = 12.97, 77.59

for p in props:
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&property={p}&depth=0-5cm&value=mean"
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CropSense-AI/1.0'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
            print(f"Prop '{p}': status {resp.status} in {time.time()-t0:.2f}s, layers: {[l['name'] for l in data['properties']['layers']]}")
    except Exception as e:
        print(f"Prop '{p}': FAILED in {time.time()-t0:.2f}s: {e}")
