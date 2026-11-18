"""
audit_karnataka_shc.py
───────────────────────
Phase 1: Full data audit of Karnataka Soil Health Card (SHC) files under research/shc_karnataka/.
"""

import os
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILES = {
    'raw_shc': os.path.join(BASE_DIR, 'karnataka_shc.csv'),
    'npk_tidy': os.path.join(BASE_DIR, 'karnataka_npk_tidy.csv'),
    'npk_wide': os.path.join(BASE_DIR, 'karnataka_npk_wide.csv'),
    'district_share': os.path.join(BASE_DIR, 'karnataka_npk_district_share.csv')
}

def audit():
    print("==================================================================")
    print("PHASE 1: KARNATAKA SOIL HEALTH CARD (SHC) DATA AUDIT")
    print("==================================================================")
    
    # 1. District Share summary file
    print("\n--- 1. karnataka_npk_district_share.csv ---")
    df_share = pd.read_csv(FILES['district_share'])
    print(f"Shape: {df_share.shape} (rows: {len(df_share)}, cols: {len(df_share.columns)})")
    print("Columns:", df_share.columns.tolist())
    print("Unique districts:", df_share['district_name'].nunique())
    print("Districts in share table:", sorted(df_share['district_name'].unique()))
    print("Head (5 rows):\n", df_share.head(5))
    
    # 2. NPK Wide
    print("\n--- 2. karnataka_npk_wide.csv ---")
    df_wide = pd.read_csv(FILES['npk_wide'])
    print(f"Shape: {df_wide.shape} (rows: {len(df_wide)}, cols: {len(df_wide.columns)})")
    print("Columns:", df_wide.columns.tolist())
    print("Dtypes:\n", df_wide.dtypes)
    print("Missing values:\n", df_wide.isnull().sum())
    print("Unique districts:", df_wide['district_name'].nunique())
    print("Unique blocks:", df_wide['block_name'].nunique())
    print("Unique villages:", df_wide['village_name'].nunique())
    print("Years:", df_wide['year'].value_counts().to_dict())
    print("Duplicate (district, block, village, year):", df_wide.duplicated(subset=['district_name', 'block_name', 'village_name', 'year']).sum())
    print("Total sample cards (sum of all N cards):", (df_wide['nitrogen_low'] + df_wide['nitrogen_medium'] + df_wide['nitrogen_high']).sum())
    
    # 3. NPK Tidy
    print("\n--- 3. karnataka_npk_tidy.csv ---")
    df_tidy = pd.read_csv(FILES['npk_tidy'])
    print(f"Shape: {df_tidy.shape} (rows: {len(df_tidy)}, cols: {len(df_tidy.columns)})")
    print("Columns:", df_tidy.columns.tolist())
    print("Unique nutrients:", df_tidy['nutrient_name'].value_counts().to_dict())
    print("Unique levels:", df_tidy['nutrient_level'].value_counts().to_dict())
    print("Total cards count by nutrient:\n", df_tidy.groupby('nutrient_name')['cards'].sum())
    
    # 4. Raw SHC inspect (chunk or read columns)
    print("\n--- 4. karnataka_shc.csv ---")
    # Read first 1000 rows to check schema and types
    df_raw_head = pd.read_csv(FILES['raw_shc'], nrows=1000)
    print("Columns in raw SHC:", df_raw_head.columns.tolist())
    print("Sample row:\n", df_raw_head.iloc[0].to_dict())
    
    # Read full raw SHC line count & basic stats
    df_raw_cols = pd.read_csv(FILES['raw_shc'], usecols=['year', 'district_name', 'nutrient_name', 'nutrient_level', 'value'])
    print(f"Raw SHC Total Rows: {len(df_raw_cols):,}")
    print("Raw SHC Unique Districts:", df_raw_cols['district_name'].nunique())
    print("Raw SHC Unique Nutrients:", df_raw_cols['nutrient_name'].unique().tolist())
    print("Raw SHC Years:", df_raw_cols['year'].value_counts().to_dict())
    print("Raw SHC Missing values:\n", df_raw_cols.isnull().sum())
    
    # Check duplicate combinations in raw SHC
    # id is usually unique
    df_raw_id = pd.read_csv(FILES['raw_shc'], usecols=['id'])
    print("Raw SHC Unique IDs:", df_raw_id['id'].nunique())
    
    # Save summary stats
    audit_results = {
        'files_inspected': list(FILES.keys()),
        'raw_shc_rows': len(df_raw_cols),
        'npk_wide_rows': len(df_wide),
        'npk_tidy_rows': len(df_tidy),
        'district_share_rows': len(df_share),
        'unique_districts': int(df_wide['district_name'].nunique()),
        'districts_list': sorted(df_wide['district_name'].unique()),
        'years': df_wide['year'].value_counts().to_dict(),
        'total_shc_nitrogen_cards': int((df_wide['nitrogen_low'] + df_wide['nitrogen_medium'] + df_wide['nitrogen_high']).sum()),
        'total_shc_phosphorus_cards': int((df_wide['phosphorus_low'] + df_wide['phosphorus_medium'] + df_wide['phosphorus_high']).sum()),
        'total_shc_potassium_cards': int((df_wide['potassium_low'] + df_wide['potassium_medium'] + df_wide['potassium_high']).sum())
    }
    
    with open(os.path.join(BASE_DIR, 'phase1_audit_stats.json'), 'w') as f:
        json.dump(audit_results, f, indent=2)
    print("\nPhase 1 stats saved to phase1_audit_stats.json")

if __name__ == '__main__':
    audit()
