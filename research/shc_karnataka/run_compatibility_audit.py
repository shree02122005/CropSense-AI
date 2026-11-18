"""
run_compatibility_audit.py
──────────────────────────
Executes comprehensive validation of data/karnataka_main_places_npk_project_ready_v2.csv
against production v1 lookup, crop model training dataset, and models/crop_model.pkl.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V1_PATH = os.path.join(ROOT_DIR, 'data', 'karnataka_main_places_npk_project_ready_v1.csv')
V2_PATH = os.path.join(ROOT_DIR, 'data', 'karnataka_main_places_npk_project_ready_v2.csv')
CROP_DATA_PATH = os.path.join(ROOT_DIR, 'datasets', 'Crop_recommendation_clean.csv')
CROP_MODEL_PATH = os.path.join(ROOT_DIR, 'models', 'crop_model.pkl')
OUT_CSV = os.path.join(ROOT_DIR, 'research', 'shc_karnataka', 'shc_vs_production_comparison.csv')

def classify_n(val):
    if val < 280: return "Low"
    elif val <= 560: return "Medium"
    else: return "High"

def classify_p(val):
    # Standard P2O5: Low < 23, Medium 23-56, High > 56
    if val < 23.0: return "Low"
    elif val <= 56.0: return "Medium"
    else: return "High"

def classify_k(val):
    # Standard K2O: Low < 144, Medium 144-336, High > 336
    if val < 144.0: return "Low"
    elif val <= 336.0: return "Medium"
    else: return "High"

def run_audit():
    print("==================================================================")
    print("AUDIT: KARNATAKA NPK LOOKUP V2 (SHC LAB AGGREGATE) VALIDATION")
    print("==================================================================")
    
    # --- Check A: Dataset Check ---
    print("\n--- Check A: Dataset Check ---")
    df_v2 = pd.read_csv(V2_PATH)
    df_v1 = pd.read_csv(V1_PATH)
    
    print(f"v2 Row Count: {len(df_v2)} rows, Columns: {len(df_v2.columns)}")
    print("Columns:", df_v2.columns.tolist())
    
    # Districts breakdown
    dist_v2 = df_v2[df_v2['district'] != 'Karnataka coverage']
    dist_v1 = df_v1[df_v1['district'] != 'Karnataka coverage']
    
    print(f"Administrative district rows in v2: {len(dist_v2)}")
    print(f"Unique districts in v2: {dist_v2['district'].nunique()}")
    print("Districts present:", sorted(dist_v2['district'].unique()))
    print(f"Duplicate districts: {dist_v2.duplicated(subset=['district']).sum()}")
    
    # Missing values
    print("Missing values in v2:\n", df_v2.isnull().sum())
    
    # Statistical summary for N, P, K
    print("\n--- Numerical Summary of v2 (31 Districts) ---")
    for nut in ['N_model_input', 'P_model_input', 'K_model_input']:
        s = dist_v2[nut]
        print(f"  {nut}: min={s.min():.1f}, 25%={s.quantile(0.25):.1f}, mean={s.mean():.1f}, median={s.median():.1f}, 75%={s.quantile(0.75):.1f}, max={s.max():.1f}, std={s.std():.1f}")
        
    print("\n--- Numerical Summary of v1 (31 Districts) ---")
    for nut in ['N_model_input', 'P_model_input', 'K_model_input']:
        s = dist_v1[nut]
        print(f"  {nut}: min={s.min():.1f}, 25%={s.quantile(0.25):.1f}, mean={s.mean():.1f}, median={s.median():.1f}, 75%={s.quantile(0.75):.1f}, max={s.max():.1f}, std={s.std():.1f}")

    print("\nSource types in v2:\n", df_v2['source_type'].value_counts())
    print("Units specified:\n", df_v2['model_unit'].value_counts())
    
    # --- Check B: Model Compatibility ---
    print("\n--- Check B: Model Compatibility (vs Crop Model Training Set) ---")
    df_crop = pd.read_csv(CROP_DATA_PATH)
    print(f"Crop Model Training Dataset: {len(df_crop)} rows")
    
    crop_stats = {}
    v2_stats = {}
    ood_analysis = {}
    
    for nut, col in [('N', 'N_model_input'), ('P', 'P_model_input'), ('K', 'K_model_input')]:
        s_tr = df_crop[nut]
        s_v2 = dist_v2[col]
        
        tr_min, tr_max, tr_mean, tr_med = s_tr.min(), s_tr.max(), s_tr.mean(), s_tr.median()
        v2_min, v2_max, v2_mean, v2_med = s_v2.min(), s_v2.max(), s_v2.mean(), s_v2.median()
        
        # OOD checks
        below_min = (s_v2 < tr_min).sum()
        above_max = (s_v2 > tr_max).sum()
        total_ood = below_min + above_max
        pct_ood = 100 * total_ood / len(s_v2)
        
        print(f"\nNutrient: {nut}")
        print(f"  Training: min={tr_min:.2f}, max={tr_max:.2f}, mean={tr_mean:.2f}, median={tr_med:.2f}")
        print(f"  v2 SHC:   min={v2_min:.2f}, max={v2_max:.2f}, mean={v2_mean:.2f}, median={v2_med:.2f}")
        print(f"  OOD Count: Below min (<{tr_min:.2f}): {below_min}, Above max (>{tr_max:.2f}): {above_max}")
        print(f"  OOD Percentage: {total_ood} / {len(s_v2)} ({pct_ood:.1f}%)")
        
        if above_max > 0:
            ood_dists = dist_v2[s_v2 > tr_max][['district', col]].to_dict(orient='records')
            print(f"  Districts above max: {ood_dists}")
            
        ood_analysis[nut] = {
            'training': {'min': tr_min, 'max': tr_max, 'mean': tr_mean, 'median': tr_med},
            'v2_shc': {'min': v2_min, 'max': v2_max, 'mean': v2_mean, 'median': v2_med},
            'below_min': int(below_min),
            'above_max': int(above_max),
            'total_ood': int(total_ood),
            'pct_ood': float(pct_ood)
        }
        
    # --- Check C & D: Prediction Shadow Test ---
    print("\n--- Check C & D: Prediction Shadow Test across 31 Districts ---")
    crop_model = joblib.load(CROP_MODEL_PATH)
    crop_classes = crop_model.classes_
    print(f"Crop Model: {type(crop_model).__name__} ({len(crop_classes)} classes)")
    
    # Controlled standard weather & soil conditions
    # Standard Karnataka Kharif conditions:
    std_temp = 26.0
    std_humidity = 68.0
    std_ph = 6.5
    std_rainfall = 120.0
    
    # Merge v1 and v2 on district
    merged = pd.merge(
        dist_v1[['district', 'reference_place', 'latitude', 'longitude', 'N_model_input', 'P_model_input', 'K_model_input', 'source_type']],
        dist_v2[['district', 'N_model_input', 'P_model_input', 'K_model_input', 'source_type']],
        on='district',
        suffixes=('_v1', '_v2')
    )
    
    shadow_records = []
    
    for _, r in merged.iterrows():
        dist = r['district']
        n1, p1, k1 = float(r['N_model_input_v1']), float(r['P_model_input_v1']), float(r['K_model_input_v1'])
        n2, p2, k2 = float(r['N_model_input_v2']), float(r['P_model_input_v2']), float(r['K_model_input_v2'])
        
        # Categorize
        n1_cat, n2_cat = classify_n(n1), classify_n(n2)
        p1_cat, p2_cat = classify_p(p1), classify_p(p2)
        k1_cat, k2_cat = classify_k(k1), classify_k(k2)
        
        cat_changed = (n1_cat != n2_cat) or (p1_cat != p2_cat) or (k1_cat != k2_cat)
        
        # Standard Red soil (encoded = 3 in backend) or Loamy (encoded = 2)
        # Let's test with soil_type_encoded = 3 (Red, typical Karnataka topsoil)
        soil_code = 3
        
        # Vector v1: [N, P, K, temp, humidity, ph, rainfall, soil_type_encoded]
        vec1 = np.array([[n1, p1, k1, std_temp, std_humidity, std_ph, std_rainfall, soil_code]])
        proba1 = crop_model.predict_proba(vec1)[0]
        top1_idx = np.argmax(proba1)
        crop1 = crop_classes[top1_idx]
        conf1 = proba1[top1_idx]
        
        # Vector v2:
        vec2 = np.array([[n2, p2, k2, std_temp, std_humidity, std_ph, std_rainfall, soil_code]])
        proba2 = crop_model.predict_proba(vec2)[0]
        top2_idx = np.argmax(proba2)
        crop2 = crop_classes[top2_idx]
        conf2 = proba2[top2_idx]
        
        rec_changed = (crop1 != crop2)
        
        shadow_records.append({
            'district': dist,
            'ref_place': r['reference_place'],
            'lat': r['latitude'],
            'lon': r['longitude'],
            'v1_N': round(n1, 1),
            'v1_P': round(p1, 1),
            'v1_K': round(k1, 1),
            'v1_N_class': n1_cat,
            'v1_P_class': p1_cat,
            'v1_K_class': k1_cat,
            'v2_N': round(n2, 1),
            'v2_P': round(p2, 1),
            'v2_K': round(k2, 1),
            'v2_N_class': n2_cat,
            'v2_P_class': p2_cat,
            'v2_K_class': k2_cat,
            'diff_N': round(n2 - n1, 1),
            'diff_P': round(p2 - p1, 1),
            'diff_K': round(k2 - k1, 1),
            'category_changed': cat_changed,
            'crop_v1': crop1,
            'conf_v1': round(conf1, 3),
            'crop_v2': crop2,
            'conf_v2': round(conf2, 3),
            'recommendation_changed': rec_changed,
            'v1_source': r['source_type_v1'],
            'v2_source': r['source_type_v2']
        })
        
    df_shadow = pd.DataFrame(shadow_records)
    df_shadow.to_csv(OUT_CSV, index=False)
    print(f"\nSaved district shadow comparison to {OUT_CSV}")
    
    n_cat_changes = df_shadow['category_changed'].sum()
    n_rec_changes = df_shadow['recommendation_changed'].sum()
    
    print(f"\n--- Shadow Comparison Summary ---")
    print(f"Districts evaluated: {len(df_shadow)}")
    print(f"Districts where N/P/K fertility category changed: {n_cat_changes} / {len(df_shadow)} ({100*n_cat_changes/len(df_shadow):.1f}%)")
    print(f"Districts where Top-1 Crop Recommendation changed: {n_rec_changes} / {len(df_shadow)} ({100*n_rec_changes/len(df_shadow):.1f}%)")
    
    print("\nCrop recommendation transitions:")
    for _, r in df_shadow[df_shadow['recommendation_changed']].iterrows():
        print(f"  {r['district']}: {r['crop_v1']} ({r['conf_v1']:.1%}) -> {r['crop_v2']} ({r['conf_v2']:.1%}) | dN={r['diff_N']:+.1f}, dP={r['diff_P']:+.1f}, dK={r['diff_K']:+.1f}")

    # Save summary json
    summary = {
        'total_districts': len(df_shadow),
        'category_changes': int(n_cat_changes),
        'recommendation_changes': int(n_rec_changes),
        'rec_change_rate': float(round(100*n_rec_changes/len(df_shadow), 1)),
        'ood_analysis': ood_analysis
    }
    with open(os.path.join(ROOT_DIR, 'research', 'shc_karnataka', 'v2_validation_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    run_audit()
