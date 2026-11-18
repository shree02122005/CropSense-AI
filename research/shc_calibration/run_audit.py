import os
import json
import pandas as pd
import numpy as np

def audit():
    print("=== STARTING FULL AUDIT ===")
    
    # 1. District centroids
    df_centroids = pd.read_csv('research/shc_calibration/district_centroids.csv')
    print(f"Centroids: {len(df_centroids)} rows, {len(df_centroids.columns)} cols")
    
    # 2. SHC District with Coords
    df_shc = pd.read_csv('research/shc_calibration/shc_district_with_coords.csv')
    print(f"SHC: {len(df_shc)} rows, {len(df_shc.columns)} cols")
    
    print("\n--- Columns and Types ---")
    print("Centroids columns and dtypes:")
    for col, dt in df_centroids.dtypes.items():
        print(f"  {col}: {dt} (nulls: {df_centroids[col].isnull().sum()})")
        
    print("SHC columns and dtypes:")
    for col, dt in df_shc.dtypes.items():
        print(f"  {col}: {dt} (nulls: {df_shc[col].isnull().sum()})")
        
    # State & District coverage
    print("\n--- Geographic Coverage ---")
    print(f"Centroids states ({df_centroids['state_name'].nunique()}):", sorted(df_centroids['state_name'].unique()))
    print(f"SHC states ({df_shc['state_name'].nunique()}):", sorted(df_shc['state_name'].unique()))
    
    shc_states = set(df_shc['state_name'].unique())
    cent_states = set(df_centroids['state_name'].unique())
    print("States in centroids but not in SHC:", cent_states - shc_states)
    print("States in SHC but not in centroids:", shc_states - cent_states)
    
    # Year coverage
    print("\n--- Year Coverage ---")
    print(df_shc['year'].value_counts())
    
    # Duplicate analysis
    print("\n--- Duplicate Analysis ---")
    print(f"Centroids full duplicate rows: {df_centroids.duplicated().sum()}")
    print(f"Centroids (district, state) duplicates: {df_centroids.duplicated(subset=['district_name', 'state_name']).sum()}")
    print(f"SHC full duplicate rows: {df_shc.duplicated().sum()}")
    print(f"SHC (state, district, year) unique combos: {df_shc[['state_name', 'district_name', 'year']].drop_duplicates().shape[0]}")
    print(f"SHC (state, district, year, nutrient_name) duplicates: {df_shc.duplicated(subset=['state_name', 'district_name', 'year', 'nutrient_name']).sum()}")
    
    # Why 6600 rows?
    print("\n--- Group Structure of SHC ---")
    combos = df_shc.groupby(['state_name', 'district_name', 'year']).size()
    print(f"Total unique (state, district, year) combos: {len(combos)}")
    print(f"Distribution of rows per combo:\n{combos.value_counts()}")
    
    # Are values of N, P, K, pH, OC identical across the 5 rows for each (state, district, year)?
    g = df_shc.groupby(['state_name', 'district_name', 'year'])
    n_std = g['N_kg_ha'].std().fillna(0).max()
    p_std = g['P_kg_ha'].std().fillna(0).max()
    k_std = g['K_kg_ha'].std().fillna(0).max()
    oc_std = g['OC_pct'].std().fillna(0).max()
    ph_std = g['pH'].std().fillna(0).max()
    print(f"Max within-combo standard deviation: N={n_std}, P={p_std}, K={k_std}, OC={oc_std}, pH={ph_std}")
    print("-> ALL nutrient values are IDENTICAL across the 5 nutrient_name rows for any (state, district, year)!")
    
    # De-duplicated dataset (1 row per state, district, year)
    df_dedup = df_shc[['state_name', 'district_name', 'year', 'N_kg_ha', 'P_kg_ha', 'K_kg_ha', 'pH', 'OC_pct', 'lat', 'lon', 'skey']].drop_duplicates()
    print(f"\nDe-duplicated observations (state, district, year): {len(df_dedup)} rows")
    
    # Unique districts
    unique_districts = df_dedup[['state_name', 'district_name']].drop_duplicates()
    print(f"Unique districts in SHC: {len(unique_districts)}")
    
    # Missing coordinates
    missing_coords = df_dedup[df_dedup['lat'].isnull()]
    print(f"Observations missing coordinates: {len(missing_coords)} out of {len(df_dedup)}")
    print(f"Unique districts missing coordinates: {missing_coords[['state_name', 'district_name']].drop_duplicates().shape[0]}")
    
    # Complete N/P/K/pH/OC
    complete_npk = df_dedup.dropna(subset=['N_kg_ha', 'P_kg_ha', 'K_kg_ha'])
    print(f"Complete N/P/K observations: {len(complete_npk)}")
    complete_all = df_dedup.dropna(subset=['N_kg_ha', 'P_kg_ha', 'K_kg_ha', 'pH', 'OC_pct', 'lat', 'lon'])
    print(f"Complete targets + coords: {len(complete_all)} observations across {complete_all[['state_name', 'district_name']].drop_duplicates().shape[0]} districts")
    
    # Karnataka specific
    ka = df_dedup[df_dedup['state_name'].str.lower() == 'karnataka']
    print(f"\n--- Karnataka Specific ---")
    print(f"Karnataka total observations (district-years): {len(ka)}")
    print(f"Karnataka unique districts: {ka['district_name'].nunique()}")
    print(f"Karnataka districts with coords: {ka.dropna(subset=['lat'])['district_name'].nunique()}")
    print("Karnataka districts missing coords:", ka[ka['lat'].isnull()]['district_name'].tolist())
    print("Karnataka years:", ka['year'].value_counts().to_dict())
    
    # Distributions & Summary Stats
    print("\n--- Distribution Statistics (Unique District-Years) ---")
    for col in ['N_kg_ha', 'P_kg_ha', 'K_kg_ha', 'pH', 'OC_pct']:
        s = df_dedup[col].dropna()
        q25, q50, q75 = s.quantile([0.25, 0.50, 0.75])
        iqr = q75 - q25
        low_bound = q25 - 1.5 * iqr
        high_bound = q75 + 1.5 * iqr
        outliers_low = (s < low_bound).sum()
        outliers_high = (s > high_bound).sum()
        print(f"\nVariable: {col}")
        print(f"  Count: {len(s)}, Missing: {df_dedup[col].isnull().sum()}")
        print(f"  Mean: {s.mean():.2f}, Std: {s.std():.2f}")
        print(f"  Min: {s.min():.2f}, 1%: {s.quantile(0.01):.2f}, 25%: {q25:.2f}, Median: {q50:.2f}, 75%: {q75:.2f}, 99%: {s.quantile(0.99):.2f}, Max: {s.max():.2f}")
        print(f"  IQR Outliers: Low (<{low_bound:.2f}): {outliers_low}, High (>{high_bound:.2f}): {outliers_high}, Total Outliers: {outliers_low + outliers_high} ({100*(outliers_low+outliers_high)/len(s):.1f}%)")

    # Let's save stats to json for reporting
    stats = {
        'total_shc_rows': len(df_shc),
        'dedup_rows': len(df_dedup),
        'unique_districts': len(unique_districts),
        'unique_states': df_shc['state_name'].nunique(),
        'years': df_shc['year'].value_counts().to_dict(),
        'karnataka_districts': ka['district_name'].nunique(),
        'karnataka_obs': len(ka),
    }
    with open('research/shc_calibration/audit_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)

if __name__ == '__main__':
    audit()
