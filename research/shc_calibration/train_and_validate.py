"""
train_and_validate.py
────────────────────
Phases 6, 7, 8, 9:
- Train separate models for Available N, P, K using RandomForestRegressor.
- 5-fold GroupKFold by district to prevent spatial leakage.
- Calculate R2, MAE, RMSE, MedAE vs naive Mean Baseline.
- Sliced validation performance for Karnataka.
- Feature importance analysis.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, median_absolute_error
import joblib

DATA_PATH = os.path.join('research', 'shc_calibration', 'shc_soilgrids_training.csv')
MODELS_DIR = os.path.join('research', 'shc_calibration', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

FEATURES = [
    'phh2o_0-5cm', 'phh2o_0-30cm',
    'soc_0-5cm', 'soc_0-30cm',
    'nitrogen_0-5cm', 'nitrogen_0-30cm',
    'clay_0-5cm', 'clay_0-30cm',
    'sand_0-5cm', 'sand_0-30cm',
    'cec_0-5cm', 'cec_0-30cm'
]

TARGETS = ['N_kg_ha', 'P_kg_ha', 'K_kg_ha']

def evaluate():
    print("=== PHASES 6-9: REGRESSION TRAINING & VALIDATION ===")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows from {DATA_PATH}")
    
    # Create unique district identifier (state + district) to avoid cross-state name collisions
    df['district_id'] = df['state_name'] + "__" + df['district_name']
    
    X = df[FEATURES]
    groups = df['district_id']
    
    gkf = GroupKFold(n_splits=5)
    
    cv_results = {}
    oof_predictions = pd.DataFrame(index=df.index)
    oof_predictions['state_name'] = df['state_name']
    oof_predictions['district_name'] = df['district_name']
    oof_predictions['year'] = df['year']
    
    for t in TARGETS:
        print(f"\n==================== TARGET: {t} ====================")
        y = df[t].values
        
        # Out-of-fold array
        oof_pred = np.zeros(len(df))
        oof_baseline = np.zeros(len(df))
        
        fold_metrics = []
        
        for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=groups)):
            X_tr, y_tr = X.iloc[train_idx], y[train_idx]
            X_val, y_val = X.iloc[val_idx], y[val_idx]
            
            # Baseline: predict train mean
            train_mean = np.mean(y_tr)
            oof_baseline[val_idx] = train_mean
            
            # Model: Random Forest
            rf = RandomForestRegressor(
                n_estimators=300,
                min_samples_leaf=3,
                max_features='sqrt',
                random_state=42 + fold,
                n_jobs=-1
            )
            rf.fit(X_tr, y_tr)
            preds = rf.predict(X_val)
            oof_pred[val_idx] = preds
            
            f_r2 = r2_score(y_val, preds)
            f_mae = mean_absolute_error(y_val, preds)
            f_rmse = np.sqrt(mean_squared_error(y_val, preds))
            f_medae = median_absolute_error(y_val, preds)
            fold_metrics.append({'fold': fold, 'r2': f_r2, 'mae': f_mae, 'rmse': f_rmse, 'medae': f_medae})
            
        oof_predictions[f"{t}_actual"] = y
        oof_predictions[f"{t}_pred"] = oof_pred
        oof_predictions[f"{t}_baseline"] = oof_baseline
        
        # Overall National Metrics
        nat_r2 = r2_score(y, oof_pred)
        nat_mae = mean_absolute_error(y, oof_pred)
        nat_rmse = np.sqrt(mean_squared_error(y, oof_pred))
        nat_medae = median_absolute_error(y, oof_pred)
        
        base_r2 = r2_score(y, oof_baseline)
        base_mae = mean_absolute_error(y, oof_baseline)
        base_rmse = np.sqrt(mean_squared_error(y, oof_baseline))
        base_medae = median_absolute_error(y, oof_baseline)
        
        print(f"NATIONAL PERFORMANCE (5-Fold GroupKFold):")
        print(f"  Model    -> R2: {nat_r2:.4f}, MAE: {nat_mae:.2f} kg/ha, RMSE: {nat_rmse:.2f} kg/ha, MedAE: {nat_medae:.2f} kg/ha")
        print(f"  Baseline -> R2: {base_r2:.4f}, MAE: {base_mae:.2f} kg/ha, RMSE: {base_rmse:.2f} kg/ha, MedAE: {base_medae:.2f} kg/ha")
        print(f"  MAE Improvement over Baseline: {base_mae - nat_mae:.2f} kg/ha ({100*(base_mae - nat_mae)/base_mae:.1f}%)")
        
        # Phase 8: Karnataka Specific Performance
        ka_mask = df['state_name'] == 'Karnataka'
        y_ka = y[ka_mask]
        pred_ka = oof_pred[ka_mask]
        base_ka = oof_baseline[ka_mask]
        
        ka_r2 = r2_score(y_ka, pred_ka)
        ka_mae = mean_absolute_error(y_ka, pred_ka)
        ka_rmse = np.sqrt(mean_squared_error(y_ka, pred_ka))
        ka_medae = median_absolute_error(y_ka, pred_ka)
        
        ka_base_r2 = r2_score(y_ka, base_ka)
        ka_base_mae = mean_absolute_error(y_ka, base_ka)
        ka_base_rmse = np.sqrt(mean_squared_error(y_ka, base_ka))
        ka_base_medae = median_absolute_error(y_ka, base_ka)
        
        print(f"KARNATAKA SLICE PERFORMANCE (n={len(y_ka)} across {df[ka_mask]['district_name'].nunique()} districts):")
        print(f"  Model    -> R2: {ka_r2:.4f}, MAE: {ka_mae:.2f} kg/ha, RMSE: {ka_rmse:.2f} kg/ha, MedAE: {ka_medae:.2f} kg/ha")
        print(f"  Baseline -> R2: {ka_base_r2:.4f}, MAE: {ka_base_mae:.2f} kg/ha, RMSE: {ka_base_rmse:.2f} kg/ha, MedAE: {ka_base_medae:.2f} kg/ha")
        
        # Phase 10: Fit final production-grade experimental model on ALL clean data
        final_rf = RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=3,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        final_rf.fit(X, y)
        
        # Feature importance
        fi = dict(zip(FEATURES, [round(float(v), 4) for v in final_rf.feature_importances_]))
        sorted_fi = dict(sorted(fi.items(), key=lambda item: item[1], reverse=True))
        print(f"FEATURE IMPORTANCE (Phase 9):")
        for feat, imp in sorted_fi.items():
            print(f"   {feat}: {imp:.4f}")
            
        # Save model
        target_slug = t.split('_')[0].lower()
        model_path = os.path.join(MODELS_DIR, f"available_{target_slug}_model.joblib")
        joblib.dump(final_rf, model_path)
        print(f"Saved experimental model to {model_path}")
        
        cv_results[t] = {
            'national': {
                'r2': round(float(nat_r2), 4),
                'mae': round(float(nat_mae), 2),
                'rmse': round(float(nat_rmse), 2),
                'medae': round(float(nat_medae), 2),
                'baseline_r2': round(float(base_r2), 4),
                'baseline_mae': round(float(base_mae), 2),
                'baseline_rmse': round(float(base_rmse), 2),
                'baseline_medae': round(float(base_medae), 2),
            },
            'karnataka': {
                'n_obs': int(len(y_ka)),
                'n_districts': int(df[ka_mask]['district_name'].nunique()),
                'r2': round(float(ka_r2), 4),
                'mae': round(float(ka_mae), 2),
                'rmse': round(float(ka_rmse), 2),
                'medae': round(float(ka_medae), 2),
                'baseline_r2': round(float(ka_base_r2), 4),
                'baseline_mae': round(float(ka_base_mae), 2),
                'baseline_rmse': round(float(ka_base_rmse), 2),
                'baseline_medae': round(float(ka_base_medae), 2),
            },
            'feature_importance': sorted_fi
        }
        
    # Save OOF predictions
    oof_predictions.to_csv('research/shc_calibration/oof_predictions.csv', index=False)
    
    # Save Metadata (Phase 10)
    metadata = {
        'training_dataset': 'research/shc_calibration/shc_soilgrids_training.csv',
        'n_observations': len(df),
        'n_districts': df['district_id'].nunique(),
        'n_states': df['state_name'].nunique(),
        'features': FEATURES,
        'model_type': 'RandomForestRegressor',
        'model_parameters': {
            'n_estimators': 300,
            'min_samples_leaf': 3,
            'max_features': 'sqrt',
            'random_state': 42
        },
        'validation_method': 'GroupKFold(n_splits=5, groups=district_id)',
        'training_date': '2026-10-06',
        'results': cv_results
    }
    
    with open('research/shc_calibration/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("\nSaved research/shc_calibration/model_metadata.json")

if __name__ == '__main__':
    evaluate()
