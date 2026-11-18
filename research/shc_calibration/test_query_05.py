import httpx
import time

def test_query():
    props = ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'cec']
    q = '&'.join([f'property={p}' for p in props] + ['depth=0-5cm', 'value=mean'])
    url = f'https://rest.isric.org/soilgrids/v2.0/properties/query?lat=12.97&lon=77.59&{q}'
    print("Testing URL:", url)
    t0 = time.time()
    try:
        r = httpx.get(url, timeout=15)
        print(f"Status: {r.status_code} in {time.time()-t0:.2f}s")
        if r.status_code == 200:
            d = r.json()
            for l in d['properties']['layers']:
                fac = l['unit_measure']['d_factor']
                for dep in l['depths']:
                    val = dep['values'].get('mean')
                    print(f"  {l['name']} {dep['label']}: raw={val}, scaled={val/fac if val else None}")
    except Exception as e:
        print("Failed:", e)

if __name__ == '__main__':
    test_query()
