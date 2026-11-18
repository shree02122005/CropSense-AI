"""
experimental_npk_provider.py
─────────────────────────────
Phase 11: Experimental NPK Provider using SHC-calibrated regression models.
DO NOT IMPORT OR CONNECT TO PRODUCTION API. RESEARCH ISOLATION ONLY.

Predicts available N, P, K (kg/ha) from SoilGrids depth-resolved covariates.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
CACHE_PATH = os.path.join(BASE_DIR, 'soilgrids_cache.json')

MODEL_VERSION = "shc_rf_v1.0.0-experimental"
REQUIRED_FEATURES = [
    'phh2o_0-5cm', 'phh2o_0-30cm',
    'soc_0-5cm', 'soc_0-30cm',
    'nitrogen_0-5cm', 'nitrogen_0-30cm',
    'clay_0-5cm', 'clay_0-30cm',
    'sand_0-5cm', 'sand_0-30cm',
    'cec_0-5cm', 'cec_0-30cm'
]

_models = {}

def _load_models():
    global _models
    if not _models:
        n_path = os.path.join(MODELS_DIR, 'available_n_model.joblib')
        p_path = os.path.join(MODELS_DIR, 'available_p_model.joblib')
        k_path = os.path.join(MODELS_DIR, 'available_k_model.joblib')
        if not (os.path.exists(n_path) and os.path.exists(p_path) and os.path.exists(k_path)):
            raise FileNotFoundError("Experimental regression models not found in research/shc_calibration/models/")
        _models['N'] = joblib.load(n_path)
        _models['P'] = joblib.load(p_path)
        _models['K'] = joblib.load(k_path)
    return _models

def predict_available_npk(lat: float, lon: float, soilgrids_covariates: dict = None) -> dict:
    """
    Predicts available N, P, K from SoilGrids covariates.
    
    Parameters:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        soilgrids_covariates: Optional dictionary containing all REQUIRED_FEATURES.
                              If omitted, checks local cache.
                              
    Returns:
        dict containing N, P, K estimates or clear failure response.
    """
    try:
        models = _load_models()
    except Exception as e:
        return {
            "success": False,
            "error": f"Model loading failure: {e}",
            "source": "SHC_REGRESSION_ERROR",
            "model_version": MODEL_VERSION
        }

    cov = {}
    if soilgrids_covariates:
        cov = soilgrids_covariates
    elif os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r') as f:
                cache = json.load(f)
            key = f"{lat:.4f}|{lon:.4f}"
            cov = cache.get(key, {})
        except Exception:
            cov = {}

    # Check that all required features are present and non-null
    missing_features = [feat for feat in REQUIRED_FEATURES if cov.get(feat) is None]
    if missing_features:
        return {
            "success": False,
            "error": f"Missing required SoilGrids covariates: {missing_features}",
            "source": "SHC_REGRESSION_FAILED",
            "model_version": MODEL_VERSION,
            "confidence_or_quality": "UNAVAILABLE"
        }

    # Construct feature vector
    try:
        feat_vals = [float(cov[f]) for f in REQUIRED_FEATURES]
        X = pd.DataFrame([feat_vals], columns=REQUIRED_FEATURES)
        
        pred_n = float(models['N'].predict(X)[0])
        pred_p = float(models['P'].predict(X)[0])
        pred_k = float(models['K'].predict(X)[0])

        return {
            "success": True,
            "N": round(pred_n, 2),
            "P": round(pred_p, 2),
            "K": round(pred_k, 2),
            "source": "SHC_REGRESSION",
            "model_version": MODEL_VERSION,
            "confidence_or_quality": "EXPERIMENTAL_MEDIUM"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Prediction failed: {e}",
            "source": "SHC_REGRESSION_FAILED",
            "model_version": MODEL_VERSION,
            "confidence_or_quality": "FAILED"
        }

if __name__ == '__main__':
    # Test on Bengaluru coordinates
    test_lat, test_lon = 12.9716, 77.5946
    res = predict_available_npk(test_lat, test_lon)
    print("Test Prediction (Bengaluru):", json.dumps(res, indent=2))
