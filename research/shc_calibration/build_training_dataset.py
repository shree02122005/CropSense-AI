"""
build_training_dataset.py
─────────────────────────
Phase 5: Build clean calibration dataset for regression models.
Joins SHC target data with SoilGrids covariates, reports data loss, missing values,
and saves research/shc_calibration/shc_soilgrids_training.csv.
"""

import os
import json
import pandas as pd
import numpy as np

SHC_RAW = os.path.join('research', 'shc_calibration', 'shc_district_with_coords.csv')
MERGED_CSV = os.path.join('research', 'shc_calibration', 'shc_with_covariates.csv')
OUT_TRAIN_CSV = os.path.join('research', 'shc_calibration', 'shc_soilgrids_training.csv')

COV_FEATURES = [
    'phh2o_0-5cm', 'phh2o_0-30cm',
    'soc_0-5cm', 'soc_0-30cm',
    'nitrogen_0-5cm', 'nitrogen_0-30cm',
    'clay_0-5cm', 'clay_0-30cm',
    'sand_0-5cm', 'sand_0-30cm',
    'cec_0-5cm', 'cec_0-30cm'
]

TARGETS = ['N_kg_ha', 'P_kg_ha', 'K_kg_ha']

def build_dataset():
    print("=== PHASE 5: BUILDING CALIBRATION DATASET ===")
    
    # 1. Raw SHC data stats
    df_raw = pd.read_csv(SHC_RAW)
    rows_raw = len(df_raw)
    df_raw_dedup = df_raw[['state_name', 'district_name', 'year', 'N_kg_ha', 'P_kg_ha', 'K_kg_ha', 'pH', 'OC_pct', 'lat', 'lon']].drop_duplicates()
    rows_dedup = len(df_raw_dedup)
    
    print(f"1. Rows in raw SHC table (with 5-fold nutrient duplication): {rows_raw}")
    print(f"2. True unique district-year SHC observations: {rows_dedup}")
    
    # 2. Merged dataset with covariates
    df_merged = pd.read_csv(MERGED_CSV)
    rows_merged = len(df_merged)
    print(f"3. Rows in merged dataset (before dropping missing covariates): {rows_merged}")
    
    # Missing targets check
    missing_targets = df_merged[TARGETS].isnull().sum().to_dict()
    print(f"4. Missing targets in merged dataset: {missing_targets}")
    
    # Missing covariates check
    missing_covs = df_merged[COV_FEATURES].isnull().sum().to_dict()
    print(f"5. Missing covariates breakdown:")
    for k, v in missing_covs.items():
        print(f"   {k}: {v} nulls ({100*v/rows_merged:.1f}%)")
        
    # Check duplicate district/year combinations
    dup_combos = df_merged.duplicated(subset=['state_name', 'district_name', 'year']).sum()
    print(f"6. Duplicate (state, district, year) combinations: {dup_combos}")
    
    # Clean training dataset: require all targets and all core SoilGrids covariates
    df_clean = df_merged.dropna(subset=TARGETS + COV_FEATURES).copy()
    rows_clean = len(df_clean)
    rows_lost = rows_merged - rows_clean
    
    print(f"7. Rows after join and dropping missing values: {rows_clean}")
    print(f"8. Rows lost due to missing coordinates or SoilGrids nulls: {rows_lost} ({100*rows_lost/rows_merged:.1f}%)")
    
    # Unique districts and states in clean training set
    unique_districts = df_clean[['state_name', 'district_name']].drop_duplicates()
    unique_states = df_clean['state_name'].nunique()
    years = df_clean['year'].value_counts().to_dict()
    print(f"9. Geographic coverage in clean training dataset:")
    print(f"   - Unique states/UTs: {unique_states}")
    print(f"   - Unique districts: {len(unique_districts)}")
    print(f"   - Observations by year: {years}")
    
    # Karnataka coverage
    ka_clean = df_clean[df_clean['state_name'] == 'Karnataka']
    print(f"10. Karnataka coverage in clean training dataset:")
    print(f"   - Observations: {len(ka_clean)}")
    print(f"   - Unique districts: {ka_clean['district_name'].nunique()}")
    print(f"   - Years: {ka_clean['year'].value_counts().to_dict()}")
    
    # Save training dataset
    df_clean.to_csv(OUT_TRAIN_CSV, index=False)
    print(f"\nSaved clean training dataset to {OUT_TRAIN_CSV}")
    
    # Save Phase 5 metrics to json
    phase5_stats = {
        'rows_raw_shc': rows_raw,
        'unique_district_years_before': rows_dedup,
        'rows_after_join_clean': rows_clean,
        'rows_lost': rows_lost,
        'pct_lost': round(100 * rows_lost / rows_merged, 2),
        'unique_districts': len(unique_districts),
        'unique_states': unique_states,
        'year_distribution': years,
        'karnataka_observations': len(ka_clean),
        'karnataka_districts': ka_clean['district_name'].nunique(),
        'covariates': COV_FEATURES,
        'targets': TARGETS
    }
    with open('research/shc_calibration/phase5_dataset_stats.json', 'w') as f:
        json.dump(phase5_stats, f, indent=2)

if __name__ == '__main__':
    build_dataset()
