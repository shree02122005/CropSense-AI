"""Step 2: attach SoilGrids covariates (pH, SOC, total N, clay, sand, CEC at 0-5
and 0-30 cm) to each district row. Two-pass: (a) geocode district centroids via
Nominatim (cached to geocode_cache.json), (b) query SoilGrids REST (retries,
backoff, cached to soilgrids_cache.json). Resumable: rerun continues from cache."""
import json, time, math, sys, urllib.request, urllib.parse, os

CACHE_GEO = 'geocode_cache.json'; CACHE_SG = 'soilgrids_cache.json'
PROPS = ['nitrogen','phh2o','soc','clay','sand','cec']
DEPTHS = ['0-5cm','0-30cm']
UA = 'SHC-calibration-research/1.0 (contact: your-email@example.com)'

def load_json(p, default):
    return json.load(open(p)) if os.path.exists(p) else default
geo = load_json(CACHE_GEO, {}); sg = load_json(CACHE_SG, {})

def get(url, timeout=25, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception as e:
            wait = 5 * (2 ** i)
            print(f'  retry {i+1} ({e}); sleep {wait}s', flush=True)
            time.sleep(wait)
    return None

def geocode(district, state):
    key = f'{district}|{state}'
    if key in geo: return geo[key]
    q = urllib.parse.quote(f'{district} district, {state}, India')
    d = get(f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1')
    res = (float(d[0]['lat']), float(d[0]['lon'])) if d else None
    geo[key] = res; json.dump(geo, open(CACHE_GEO,'w'))
    time.sleep(1.1)  # Nominatim usage policy
    return res

def soilgrids(lat, lon):
    key = f'{lat:.3f}|{lon:.3f}'
    if key in sg: return sg[key]
    q = '&'.join([f'property={p}' for p in PROPS] + [f'depth={d}' for d in DEPTHS] + ['value=mean'])
    d = get(f'https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&{q}')
    if not d or 'properties' not in d: sg[key] = None; return None
    out = {}
    for layer in d['properties']['layers']:
        fac = layer['unit_measure']['d_factor']
        for dep in layer['depths']:
            if dep['values'].get('mean') is None: continue
            out[f"{layer['name']}_{dep['label']}"] = dep['values']['mean'] / fac
    sg[key] = out; json.dump(sg, open(CACHE_SG,'w'))
    return out

def main():
    import pandas as pd
    df = pd.read_csv('shc_district_targets.csv')
    if os.path.exists('shc_with_covariates.csv'):
        done = pd.read_csv('shc_with_covariates.csv')
        have = set(zip(done.state_name, done.district_name, done.year))
        df = df[~df.apply(lambda r: (r.state_name, r.district_name, r.year) in have, axis=1)]
    print('rows to process:', len(df), flush=True)
    for i, r in enumerate(df.itertuples(index=False)):
        lat, lon = geocode(r.district_name, r.state_name)
        row = {'state_name': r.state_name, 'district_name': r.district_name, 'year': r.year}
        if lat is None:
            print(f'{i+1} GEOCODE FAIL {r.district_name}/{r.state_name}', flush=True)
        else:
            cov = soilgrids(lat, lon) or {}
            row.update({'lat': lat, 'lon': lon, **cov})
        pd.DataFrame([row]).to_csv('shc_with_covariates.csv', mode='a', header=not os.path.exists('shc_with_covariates.csv'), index=False)
        if (i+1) % 25 == 0: print(f'{i+1}/{len(df)} done; sg cache={len(sg)}', flush=True)
    print('COMPLETE' if len(df)==0 else 'DONE batch', flush=True)

if __name__ == '__main__':
    sys.exit(main())
