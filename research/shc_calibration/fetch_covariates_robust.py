"""
fetch_covariates_robust.py
──────────────────────────
Step 2 & 4: Attach SoilGrids covariates (pH, SOC, total N, clay, sand, CEC at 0-5cm and 0-30cm)
to SHC district observations.

Enhancements over original fetch_soilgrids.py:
1. Uses pre-existing coordinates from shc_district_with_coords.csv and district_centroids.csv.
2. Fixes SoilGrids REST v2.0 depth querying (queries 0-5cm, 5-15cm, 15-30cm and computes 0-30cm depth-weighted mean).
3. Thread-safe disk caching (soilgrids_cache.json) and resumability.
4. Concurrency (4 workers) with exponential backoff retries.
5. Prioritizes Karnataka districts first to ensure 100% complete Karnataka data immediately.
6. Records all failed coordinates to soilgrids_failed.json.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import numpy as np

CACHE_SG = os.path.join('research', 'shc_calibration', 'soilgrids_cache.json')
FAILED_FILE = os.path.join('research', 'shc_calibration', 'soilgrids_failed.json')
OUT_CSV = os.path.join('research', 'shc_calibration', 'shc_with_covariates.csv')

PROPS = ['nitrogen', 'phh2o', 'soc', 'clay', 'sand', 'cec']
DEPTHS = ['0-5cm', '5-15cm', '15-30cm']
UA = 'CropSense-AI-Research/1.0 (contact: cropsense-research@example.com)'

# Load existing cache
if os.path.exists(CACHE_SG):
    with open(CACHE_SG, 'r') as f:
        sg_cache = json.load(f)
else:
    sg_cache = {}

if os.path.exists(FAILED_FILE):
    with open(FAILED_FILE, 'r') as f:
        failed_cache = json.load(f)
else:
    failed_cache = {}

def get_soilgrids_data(lat, lon, timeout=20, max_retries=3):
    key = f"{lat:.4f}|{lon:.4f}"
    if key in sg_cache and sg_cache[key] is not None:
        return key, sg_cache[key]
    
    q = '&'.join([f'property={p}' for p in PROPS] + [f'depth={d}' for d in DEPTHS] + ['value=mean'])
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lat={lat}&lon={lon}&{q}"
    
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    data = json.load(resp)
                    layers = data.get('properties', {}).get('layers', [])
                    if not layers:
                        return key, None
                    
                    cov = {}
                    for l in layers:
                        name = l['name']
                        fac = l['unit_measure']['d_factor']
                        depth_vals = {}
                        for dep in l['depths']:
                            raw_val = dep['values'].get('mean')
                            depth_vals[dep['label']] = raw_val / fac if raw_val is not None else None
                        
                        # Store 0-5cm
                        cov[f"{name}_0-5cm"] = depth_vals.get('0-5cm')
                        
                        # Compute depth-weighted 0-30cm mean: (5*v1 + 10*v2 + 15*v3)/30
                        v1 = depth_vals.get('0-5cm')
                        v2 = depth_vals.get('5-15cm')
                        v3 = depth_vals.get('15-30cm')
                        if v1 is not None and v2 is not None and v3 is not None:
                            cov[f"{name}_0-30cm"] = round((5.0 * v1 + 10.0 * v2 + 15.0 * v3) / 30.0, 3)
                        elif v1 is not None:
                            cov[f"{name}_0-30cm"] = v1
                        else:
                            cov[f"{name}_0-30cm"] = None
                            
                    return key, cov
        except Exception as e:
            wait = 2 * (attempt + 1)
            time.sleep(wait)
            
    return key, None

def save_cache():
    with open(CACHE_SG, 'w') as f:
        json.dump(sg_cache, f, indent=2)
    with open(FAILED_FILE, 'w') as f:
        json.dump(failed_cache, f, indent=2)

def run():
    print("=== Fetching SoilGrids Covariates ===")
    df_shc = pd.read_csv('research/shc_calibration/shc_district_with_coords.csv')
    df_cent = pd.read_csv('research/shc_calibration/district_centroids.csv')
    
    # Fill in Chamarajanagar from Chamarajanagara
    cham = df_cent[(df_cent['state_name'] == 'Karnataka') & (df_cent['district_name'] == 'Chamarajanagara')]
    if len(cham):
        c_lat, c_lon = cham.iloc[0]['lat'], cham.iloc[0]['lon']
        mask = (df_shc['state_name'] == 'Karnataka') & (df_shc['district_name'] == 'Chamarajanagar')
        df_shc.loc[mask, 'lat'] = c_lat
        df_shc.loc[mask, 'lon'] = c_lon
        print(f"Patched Chamarajanagar coords: ({c_lat}, {c_lon})")
        
    # Get unique coordinates to fetch
    valid_coords = df_shc.dropna(subset=['lat', 'lon'])[['state_name', 'district_name', 'lat', 'lon']].drop_duplicates()
    
    # Sort so Karnataka is first!
    valid_coords['is_ka'] = (valid_coords['state_name'] == 'Karnataka').astype(int)
    valid_coords = valid_coords.sort_values(by=['is_ka'], ascending=False).reset_index(drop=True)
    
    unique_points = valid_coords[['lat', 'lon']].drop_duplicates().values.tolist()
    print(f"Total unique coordinates to process: {len(unique_points)}")
    print(f"Already in cache: {len(sg_cache)}")
    
    to_fetch = [(lat, lon) for lat, lon in unique_points if f"{lat:.4f}|{lon:.4f}" not in sg_cache]
    print(f"Coordinates remaining to fetch: {len(to_fetch)}")
    
    success_count = 0
    fail_count = 0
    
    if to_fetch:
        print("Starting concurrent fetching (4 workers)...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_pt = {executor.submit(get_soilgrids_data, lat, lon): (lat, lon) for lat, lon in to_fetch}
            done_idx = 0
            for future in as_completed(future_to_pt):
                done_idx += 1
                lat, lon = future_to_pt[future]
                try:
                    key, cov = future.result()
                    if cov is not None:
                        sg_cache[key] = cov
                        success_count += 1
                    else:
                        failed_cache[key] = {'lat': lat, 'lon': lon, 'error': 'Timeout or Null after retries'}
                        fail_count += 1
                except Exception as exc:
                    key = f"{lat:.4f}|{lon:.4f}"
                    failed_cache[key] = {'lat': lat, 'lon': lon, 'error': str(exc)}
                    fail_count += 1
                    
                if done_idx % 15 == 0 or done_idx == len(to_fetch):
                    print(f"Progress: {done_idx}/{len(to_fetch)} processed ({success_count} succeeded, {fail_count} failed)")
                    save_cache()
                    
        save_cache()
        print("Finished network fetch.")
    
    print(f"Total entries in SoilGrids cache: {len(sg_cache)}")
    print(f"Total failed entries: {len(failed_cache)}")
    
    # Now build shc_with_covariates.csv
    print("\nMerging covariates into SHC dataset...")
    
    cov_rows = []
    # De-duplicate SHC to 1 row per (state, district, year)
    df_dedup = df_shc[['state_name', 'district_name', 'year', 'N_kg_ha', 'P_kg_ha', 'K_kg_ha', 'pH', 'OC_pct', 'lat', 'lon']].drop_duplicates()
    
    for row in df_dedup.itertuples(index=False):
        d = row._asdict()
        if pd.notnull(row.lat) and pd.notnull(row.lon):
            key = f"{row.lat:.4f}|{row.lon:.4f}"
            cov = sg_cache.get(key)
            if cov:
                d.update(cov)
        cov_rows.append(d)
        
    df_merged = pd.DataFrame(cov_rows)
    df_merged.to_csv(OUT_CSV, index=False)
    print(f"Saved merged dataset to {OUT_CSV} with shape {df_merged.shape}")
    
    # Check completeness
    cov_cols = [c for c in df_merged.columns if any(c.startswith(p) for p in PROPS)]
    print(f"Covariate columns present: {cov_cols}")
    non_null_cov = df_merged.dropna(subset=cov_cols)
    print(f"Observations with 100% complete SoilGrids covariates: {len(non_null_cov)} / {len(df_merged)}")
    
    ka_merged = df_merged[df_merged['state_name'] == 'Karnataka']
    ka_complete = ka_merged.dropna(subset=cov_cols)
    print(f"Karnataka complete observations: {len(ka_complete)} / {len(ka_merged)}")

if __name__ == '__main__':
    run()
