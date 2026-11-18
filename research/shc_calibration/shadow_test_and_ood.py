"""
shadow_test_and_ood.py
──────────────────────
Phases 13 & 14:
- End-to-end shadow test comparing current production Karnataka NPK lookup vs experimental regression NPK.
- Feeds both sets of NPK through production crop model (models/crop_model.pkl) without altering production code.
- Records crop recommendation changes and confidence impact.
- Evaluates Out-Of-Distribution (OOD) risks between crop model training data and regression outputs.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

# Add root directory to sys.path so we can read backend.npk_lookup and load crop_model
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from backend.npk_lookup import get_nearest_npk

CROP_MODEL_PATH = os.path.join(ROOT_DIR, 'models', 'crop_model.pkl')
CROP_DATA_PATH = os.path.join(ROOT_DIR, 'datasets', 'Crop_recommendation_clean.csv')
SHC_TRAIN_DATA = os.path.join('research', 'shc_calibration', 'shc_soilgrids_training.csv')
MODELS_DIR = os.path.join('research', 'shc_calibration', 'models')

REPRESENTATIVE_LOCATIONS = [
    {"name": "Bengaluru Urban", "lat": 12.9716, "lon": 77.5946, "soil_type": 3, "zone": "Eastern Dry Zone"},
    {"name": "Mysuru",          "lat": 12.2958, "lon": 76.6394, "soil_type": 4, "zone": "Southern Dry Zone"},
    {"name": "Hassan",          "lat": 13.0068, "lon": 76.1004, "soil_type": 4, "zone": "Southern Transition Zone"},
    {"name": "Kodagu (Madikeri)", "lat": 12.4244, "lon": 75.7382, "soil_type": 4, "zone": "Hilly / Western Ghats"},
    {"name": "Belagavi",        "lat": 15.8497, "lon": 74.4977, "soil_type": 0, "zone": "Northern Transition Zone"},
    {"name": "Kalaburagi",      "lat": 17.3297, "lon": 76.8343, "soil_type": 0, "zone": "North Eastern Dry Zone"},
    {"name": "Raichur",         "lat": 16.2076, "lon": 77.3463, "soil_type": 0, "zone": "North Eastern Dry Zone"},
    {"name": "Dharwad",         "lat": 15.4589, "lon": 75.0078, "soil_type": 0, "zone": "Northern Transition Zone"},
    {"name": "Shivamogga",      "lat": 13.9299, "lon": 75.5681, "soil_type": 4, "zone": "Southern Transition Zone"},
    {"name": "Udupi / Coastal", "lat": 13.3409, "lon": 74.7421, "soil_type": 2, "zone": "Coastal Zone"},
]

FEATURES = [
    'phh2o_0-5cm', 'phh2o_0-30cm',
    'soc_0-5cm', 'soc_0-30cm',
    'nitrogen_0-5cm', 'nitrogen_0-30cm',
    'clay_0-5cm', 'clay_0-30cm',
    'sand_0-5cm', 'sand_0-30cm',
    'cec_0-5cm', 'cec_0-30cm'
]

def run_shadow_and_ood():
    print("=== PHASE 13 & 14: END-TO-END SHADOW TEST & OOD ANALYSIS ===")
    
    # 1. Load crop model
    crop_model = joblib.load(CROP_MODEL_PATH)
    crop_classes = crop_model.classes_
    print(f"Loaded production crop model: {type(crop_model).__name__} with {len(crop_classes)} classes")
    
    # 2. Load regression models
    n_model = joblib.load(os.path.join(MODELS_DIR, 'available_n_model.joblib'))
    p_model = joblib.load(os.path.join(MODELS_DIR, 'available_p_model.joblib'))
    k_model = joblib.load(os.path.join(MODELS_DIR, 'available_k_model.joblib'))
    
    # 3. Load SoilGrids cache
    with open('research/shc_calibration/soilgrids_cache.json', 'r') as f:
        sg_cache = json.load(f)
        
    # Phase 13: Shadow Test on Representative Karnataka Locations
    print("\n--- Phase 13: Representative Locations Shadow Comparison ---")
    shadow_records = []
    
    # Fixed standard agro-climatic conditions for Karnataka kharif/rabi season
    std_temp = 26.5
    std_humidity = 68.0
    std_ph = 6.5
    std_rainfall = 115.0
    
    for loc in REPRESENTATIVE_LOCATIONS:
        lat, lon = loc['lat'], loc['lon']
        # Lookup values
        lookup = get_nearest_npk(lat, lon)
        n_look, p_look, k_look = float(lookup['N']), float(lookup['P']), float(lookup['K'])
        
        # Experimental regression values
        # Find nearest point in sg_cache that has complete non-null features
        best_pt = None
        best_d = float('inf')
        for k_pt, c_data in sg_cache.items():
            if not c_data or not all(c_data.get(f) is not None for f in FEATURES):
                continue
            p_lat, p_lon = map(float, k_pt.split('|'))
            d = (lat - p_lat)**2 + (lon - p_lon)**2
            if d < best_d:
                best_d = d
                best_pt = k_pt
                
        if best_pt is None:
            print(f"Skipping {loc['name']} - no valid SoilGrids point found")
            continue
            
        cov = sg_cache[best_pt]
        feat_vals = [float(cov[f]) for f in FEATURES]
        X_df = pd.DataFrame([feat_vals], columns=FEATURES)
        
        n_reg = float(n_model.predict(X_df)[0])
        p_reg = float(p_model.predict(X_df)[0])
        k_reg = float(k_model.predict(X_df)[0])
        
        # Model predictions
        soil_code = loc['soil_type']
        
        # Production vector: [N, P, K, temp, humidity, ph, rainfall, soil_type]
        vec_look = np.array([[n_look, p_look, k_look, std_temp, std_humidity, std_ph, std_rainfall, soil_code]])
        proba_look = crop_model.predict_proba(vec_look)[0]
        top1_look_idx = np.argmax(proba_look)
        top1_look_crop = crop_classes[top1_look_idx]
        top1_look_conf = proba_look[top1_look_idx]
        
        # Experimental vector: [N_reg, P_reg, K_reg, temp, humidity, ph, rainfall, soil_type]
        vec_reg = np.array([[n_reg, p_reg, k_reg, std_temp, std_humidity, std_ph, std_rainfall, soil_code]])
        proba_reg = crop_model.predict_proba(vec_reg)[0]
        top1_reg_idx = np.argmax(proba_reg)
        top1_reg_crop = crop_classes[top1_reg_idx]
        top1_reg_conf = proba_reg[top1_reg_idx]
        
        crop_changed = (top1_look_crop != top1_reg_crop)
        
        rec = {
            'location': loc['name'],
            'zone': loc['zone'],
            'lat': lat,
            'lon': lon,
            'lookup_N': round(n_look, 1),
            'lookup_P': round(p_look, 1),
            'lookup_K': round(k_look, 1),
            'reg_N': round(n_reg, 1),
            'reg_P': round(p_reg, 1),
            'reg_K': round(k_reg, 1),
            'diff_N': round(n_reg - n_look, 1),
            'diff_P': round(p_reg - p_look, 1),
            'diff_K': round(k_reg - k_look, 1),
            'pct_diff_N': round(100 * (n_reg - n_look) / n_look, 1),
            'pct_diff_P': round(100 * (p_reg - p_look) / p_look, 1),
            'pct_diff_K': round(100 * (k_reg - k_look) / k_look, 1),
            'crop_lookup': top1_look_crop,
            'conf_lookup': round(top1_look_conf, 3),
            'crop_reg': top1_reg_crop,
            'conf_reg': round(top1_reg_conf, 3),
            'crop_changed': crop_changed
        }
        shadow_records.append(rec)
        print(f"\n{loc['name']} ({loc['zone']}):")
        print(f"  Lookup NPK:     N={n_look:.1f}, P={p_look:.1f}, K={k_look:.1f} -> {top1_look_crop} ({top1_look_conf:.1%})")
        print(f"  Regression NPK: N={n_reg:.1f}, P={p_reg:.1f}, K={k_reg:.1f} -> {top1_reg_crop} ({top1_reg_conf:.1%})")
        print(f"  Differences:    d_N={n_reg-n_look:+.1f} ({rec['pct_diff_N']:+.1f}%), d_P={p_reg-p_look:+.1f} ({rec['pct_diff_P']:+.1f}%), d_K={k_reg-k_look:+.1f} ({rec['pct_diff_K']:+.1f}%)")
        print(f"  Crop Changed?   {'YES (CHANGED)' if crop_changed else 'NO (Maintained)'}")
        
    df_shadow = pd.DataFrame(shadow_records)
    df_shadow.to_csv('research/shc_calibration/shadow_test_results.csv', index=False)
    
    change_rate = df_shadow['crop_changed'].mean()
    print(f"\nOVERALL SHADOW RESULTS: Crop changed in {df_shadow['crop_changed'].sum()}/{len(df_shadow)} locations ({change_rate:.1%})!")
    
    # Phase 14: Out-Of-Distribution (OOD) Analysis
    print("\n--- Phase 14: Out-Of-Distribution (OOD) Analysis ---")
    df_crop_data = pd.read_csv(CROP_DATA_PATH)
    df_train_shc = pd.read_csv(SHC_TRAIN_DATA)
    
    # Regression outputs across the national calibration set
    X_all = df_train_shc[FEATURES]
    reg_n_all = n_model.predict(X_all)
    reg_p_all = p_model.predict(X_all)
    reg_k_all = k_model.predict(X_all)
    
    ood_stats = {}
    for nutrient in ['N', 'P', 'K']:
        s_crop = df_crop_data[nutrient]
        s_reg = pd.Series(reg_n_all if nutrient == 'N' else (reg_p_all if nutrient == 'P' else reg_k_all))
        
        c_min, c_q25, c_med, c_q75, c_max = s_crop.min(), s_crop.quantile(0.25), s_crop.median(), s_crop.quantile(0.75), s_crop.max()
        r_min, r_q25, r_med, r_q75, r_max = s_reg.min(), s_reg.quantile(0.25), s_reg.median(), s_reg.quantile(0.75), s_reg.max()
        
        # Out of bounds count
        below_min = (s_reg < c_min).sum()
        above_max = (s_reg > c_max).sum()
        total_ood = below_min + above_max
        pct_ood = 100 * total_ood / len(s_reg)
        
        print(f"\nNutrient: {nutrient} (kg/ha)")
        print(f"  Crop Model Training Set: Min={c_min:.2f}, 25%={c_q25:.2f}, Median={c_med:.2f}, 75%={c_q75:.2f}, Max={c_max:.2f}")
        print(f"  Regression Outputs (n={len(s_reg)}): Min={r_min:.2f}, 25%={r_q25:.2f}, Median={r_med:.2f}, 75%={r_q75:.2f}, Max={r_max:.2f}")
        print(f"  OOD Count: Below Training Min (<{c_min:.2f}): {below_min}, Above Training Max (>{c_max:.2f}): {above_max}")
        print(f"  Total OOD: {total_ood} / {len(s_reg)} ({pct_ood:.2f}%)")
        
        ood_stats[nutrient] = {
            'crop_training': {'min': c_min, 'q25': c_q25, 'median': c_med, 'q75': c_q75, 'max': c_max},
            'regression_outputs': {'min': round(r_min, 2), 'q25': round(r_q25, 2), 'median': round(r_med, 2), 'q75': round(r_q75, 2), 'max': round(r_max, 2)},
            'below_min': int(below_min),
            'above_max': int(above_max),
            'total_ood': int(total_ood),
            'pct_ood': round(pct_ood, 2)
        }
        
    with open('research/shc_calibration/ood_analysis.json', 'w') as f:
        json.dump(ood_stats, f, indent=2)
        
    print("\nSaved research/shc_calibration/shadow_test_results.csv and research/shc_calibration/ood_analysis.json")

if __name__ == '__main__':
    run_shadow_and_ood()
