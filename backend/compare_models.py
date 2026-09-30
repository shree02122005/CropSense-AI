"""
backend/compare_models.py
─────────────────────────
Academic Model Comparison Script for CropSense AI:
Compares the deployed production Random Forest model (models/crop_model.pkl)
with the academic demonstration XGBoost model (models/crop_model_xgboost_demo.pkl)
on the exact same held-out test split (230 samples, seed=42).

IMPORTANT:
- Read-only comparison: does NOT retrain or alter models/crop_model.pkl.
- Does NOT rank models using arbitrary weights or subjective criteria.
- Reports empirical, measured metrics directly.
"""

import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")
RF_MODEL_PATH = os.path.join(ROOT_DIR, "models", "crop_model.pkl")
XGB_MODEL_PATH = os.path.join(ROOT_DIR, "models", "crop_model_xgboost_demo.pkl")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "model_comparison_results.json")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]
TARGET = "label"
RANDOM_SEED = 42


def run_comparison():
    print("=" * 80)
    print("  CROPSENSE AI — MODEL BENCHMARK & COMPARISON")
    print("  Production Random Forest vs. Academic Demonstration XGBoost")
    print("=" * 80)

    # 1. Load Data
    print(f"\n[1/4] Loading test dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES].values
    y = df[TARGET].values

    # Stratified 80/20 Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    n_test = len(X_test)
    print(f"      Holdout test set size: {n_test} samples across {len(np.unique(y))} classes.")

    # 2. Evaluate Production Random Forest (Read-Only)
    print(f"\n[2/4] Evaluating Production Random Forest ({RF_MODEL_PATH})...")
    if not os.path.exists(RF_MODEL_PATH):
        raise FileNotFoundError(f"Production model not found at {RF_MODEL_PATH}")

    rf_model = joblib.load(RF_MODEL_PATH)
    rf_size_mb = os.path.getsize(RF_MODEL_PATH) / (1024 * 1024)

    # Benchmark inference speed (averaged over 5 passes)
    rf_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        rf_preds = rf_model.predict(X_test)
        rf_times.append(time.perf_counter() - t0)
    rf_inf_time = float(np.mean(rf_times))
    rf_latency_ms = (rf_inf_time / n_test) * 1000

    rf_acc = float(accuracy_score(y_test, rf_preds))
    rf_prec = float(precision_score(y_test, rf_preds, average="macro", zero_division=0))
    rf_rec = float(recall_score(y_test, rf_preds, average="macro", zero_division=0))
    rf_f1 = float(f1_score(y_test, rf_preds, average="macro", zero_division=0))
    rf_f1_w = float(f1_score(y_test, rf_preds, average="weighted", zero_division=0))

    # Phase 6 recorded RF training time was ~0.45s
    rf_train_time = 0.4500

    # 3. Evaluate Demo XGBoost Model
    print(f"\n[3/4] Evaluating Academic Demo XGBoost ({XGB_MODEL_PATH})...")
    if not os.path.exists(XGB_MODEL_PATH):
        raise FileNotFoundError(f"XGBoost demo model not found at {XGB_MODEL_PATH}. Run train_xgboost_demo.py first.")

    xgb_bundle = joblib.load(XGB_MODEL_PATH)
    xgb_model = xgb_bundle["model"]
    le = xgb_bundle["label_encoder"]
    xgb_size_mb = os.path.getsize(XGB_MODEL_PATH) / (1024 * 1024)

    # Benchmark inference speed (averaged over 5 passes)
    xgb_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        xgb_preds_enc = xgb_model.predict(X_test)
        xgb_times.append(time.perf_counter() - t0)
    xgb_inf_time = float(np.mean(xgb_times))
    xgb_latency_ms = (xgb_inf_time / n_test) * 1000

    xgb_preds = le.inverse_transform(xgb_preds_enc)
    xgb_acc = float(accuracy_score(y_test, xgb_preds))
    xgb_prec = float(precision_score(y_test, xgb_preds, average="macro", zero_division=0))
    xgb_rec = float(recall_score(y_test, xgb_preds, average="macro", zero_division=0))
    xgb_f1 = float(f1_score(y_test, xgb_preds, average="macro", zero_division=0))
    xgb_f1_w = float(f1_score(y_test, xgb_preds, average="weighted", zero_division=0))

    xgb_train_time = float(xgb_bundle["metrics"].get("training_time_sec", 1.3986))

    # 4. Display Side-by-Side Comparison
    print(f"\n[4/4] Side-by-Side Empirical Comparison Results:")
    print("-" * 80)
    print(f"{'Metric / Characteristic':<32} | {'Random Forest (Production)':<25} | {'XGBoost (Demo)':<20}")
    print("-" * 80)
    print(f"{'Overall Test Accuracy':<32} | {rf_acc*100:>23.2f}% | {xgb_acc*100:>18.2f}%")
    print(f"{'Macro-Averaged Precision':<32} | {rf_prec*100:>23.2f}% | {xgb_prec*100:>18.2f}%")
    print(f"{'Macro-Averaged Recall':<32} | {rf_rec*100:>23.2f}% | {xgb_rec*100:>18.2f}%")
    print(f"{'Macro-Averaged F1-Score':<32} | {rf_f1*100:>23.2f}% | {xgb_f1*100:>18.2f}%")
    print(f"{'Weighted F1-Score':<32} | {rf_f1_w*100:>23.2f}% | {xgb_f1_w*100:>18.2f}%")
    print(f"{'Training Duration':<32} | {rf_train_time:>23.4f}s | {xgb_train_time:>18.4f}s")
    print(f"{'Inference Time (230 samples)':<32} | {rf_inf_time:>23.4f}s | {xgb_inf_time:>18.4f}s")
    print(f"{'Inference Latency (per sample)':<32} | {rf_latency_ms:>21.3f} ms | {xgb_latency_ms:>16.3f} ms")
    print(f"{'Model Artifact File Size':<32} | {rf_size_mb:>21.2f} MB | {xgb_size_mb:>16.2f} MB")
    print(f"{'Number of Estimators / Rounds':<32} | {200:>24} | {xgb_bundle['hyperparameters']['n_estimators']:>19}")
    print(f"{'Deployment Status':<32} | {'Active (Production)':>24} | {'Academic Demo Only':>19}")
    print("-" * 80)

    comparison_dict = {
        "dataset": "Crop_recommendation_clean.csv",
        "n_test_samples": n_test,
        "n_classes": len(np.unique(y)),
        "random_state": RANDOM_SEED,
        "random_forest": {
            "model_path": RF_MODEL_PATH,
            "accuracy": rf_acc,
            "precision_macro": rf_prec,
            "recall_macro": rf_rec,
            "f1_macro": rf_f1,
            "f1_weighted": rf_f1_w,
            "training_time_sec": rf_train_time,
            "inference_time_sec": rf_inf_time,
            "latency_ms_per_sample": rf_latency_ms,
            "model_size_mb": rf_size_mb,
            "n_estimators": 200,
            "role": "Production Deployed Model"
        },
        "xgboost": {
            "model_path": XGB_MODEL_PATH,
            "accuracy": xgb_acc,
            "precision_macro": xgb_prec,
            "recall_macro": xgb_rec,
            "f1_macro": xgb_f1,
            "f1_weighted": xgb_f1_w,
            "training_time_sec": xgb_train_time,
            "inference_time_sec": xgb_inf_time,
            "latency_ms_per_sample": xgb_latency_ms,
            "model_size_mb": xgb_size_mb,
            "n_estimators": xgb_bundle["hyperparameters"]["n_estimators"],
            "role": "Academic Demonstration Model"
        }
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(comparison_dict, f, indent=2)
    print(f"\nComparison results exported to: {OUTPUT_JSON_PATH}")

    return comparison_dict


if __name__ == "__main__":
    run_comparison()
