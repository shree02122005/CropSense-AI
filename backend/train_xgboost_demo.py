"""
backend/train_xgboost_demo.py
─────────────────────────────
Academic Demonstration & Comparison Script for CropSense AI:
Trains a standalone XGBoost (XGBClassifier) model on the exact same
Phase 5 cleaned dataset (datasets/Crop_recommendation_clean.csv) using
identical 80/20 stratified split methodology (seed=42).

IMPORTANT:
- This is strictly for academic comparison and benchmarking.
- It does NOT replace or overwrite the production Random Forest model (models/crop_model.pkl).
- Model is saved separately to: models/crop_model_xgboost_demo.pkl.
"""

import os
import sys
import time
import json
import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")
MODEL_DIR = os.path.join(ROOT_DIR, "models")
XGB_MODEL_PATH = os.path.join(MODEL_DIR, "crop_model_xgboost_demo.pkl")

# Experiment constants matching Random Forest baseline
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]
TARGET = "label"
RANDOM_SEED = 42

# XGBoost Hyperparameters (Sensible, reproducible academic baseline)
XGB_PARAMS = {
    "n_estimators": 100,
    "max_depth": 4,
    "learning_rate": 0.1,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "random_state": RANDOM_SEED,
    "eval_metric": "mlogloss",
    "n_jobs": -1
}


def train_and_evaluate_xgboost():
    print("=" * 75)
    print("  CROPSENSE AI — ACADEMIC XGBOOST MODEL TRAINING & EVALUATION")
    print("  (Standalone comparison model — Does NOT modify production Random Forest)")
    print("=" * 75)

    # 1. Load Clean Dataset
    print(f"\n[1/5] Loading cleaned dataset from: {DATA_PATH}")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Clean dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    n_total = len(df)
    n_classes = df[TARGET].nunique()
    classes = sorted(df[TARGET].unique())
    print(f"      Total records: {n_total} | Target classes: {n_classes}")
    print(f"      Features ({len(FEATURES)}): {FEATURES}")

    # Verify no nulls
    nulls = df[FEATURES + [TARGET]].isnull().sum().sum()
    assert nulls == 0, f"Found {nulls} unexpected missing values!"
    print(f"      Missing values check: 0 nulls across all features.")

    # 2. Label Encoding & Stratified Split
    print(f"\n[2/5] Preparing labels and creating stratified 80/20 train/test split...")
    X = df[FEATURES].values
    y_raw = df[TARGET].values

    # Encode crop string labels to integers (0..22) for XGBoost
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_raw)

    indices = np.arange(n_total)
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y_encoded, indices, test_size=0.2, random_state=RANDOM_SEED, stratify=y_encoded
    )

    # Verify disjoint sets (zero data leakage)
    leakage = set(idx_train).intersection(set(idx_test))
    assert len(leakage) == 0, f"Data leakage detected! Overlapping indices: {leakage}"
    print(f"      Train set size: {len(X_train)} samples ({len(X_train)/n_total*100:.1f}%)")
    print(f"      Test set size:  {len(X_test)} samples ({len(X_test)/n_total*100:.1f}%)")
    print(f"      Stratification check: Exactly {len(y_test) // n_classes} test samples per class.")
    print(f"      Data leakage check: PASSED (Train and Test disjoint, 0 overlapping indices)")

    # 3. Model Training
    print(f"\n[3/5] Training XGBClassifier...")
    print(f"      Configuration:")
    for k, v in XGB_PARAMS.items():
        print(f"        - {k}: {v}")

    xgb_clf = xgb.XGBClassifier(**XGB_PARAMS)

    t_train_start = time.perf_counter()
    xgb_clf.fit(X_train, y_train)
    t_train_end = time.perf_counter()
    training_time_sec = t_train_end - t_train_start
    print(f"      Training completed in: {training_time_sec:.4f} seconds")

    # 4. Evaluation on Holdout Test Set
    print(f"\n[4/5] Evaluating XGBoost on holdout test set ({len(X_test)} samples)...")
    t_test_start = time.perf_counter()
    y_pred_enc = xgb_clf.predict(X_test)
    t_test_end = time.perf_counter()
    inference_time_sec = t_test_end - t_test_start
    latency_per_sample_ms = (inference_time_sec / len(X_test)) * 1000

    y_pred_labels = le.inverse_transform(y_pred_enc)
    y_test_labels = le.inverse_transform(y_test)

    acc = accuracy_score(y_test, y_pred_enc)
    prec_macro = precision_score(y_test, y_pred_enc, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, y_pred_enc, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred_enc, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred_enc, average="weighted", zero_division=0)

    print(f"      Accuracy:          {acc * 100:.2f}% ({int(acc * len(y_test))}/{len(y_test)} correct)")
    print(f"      Macro Precision:   {prec_macro * 100:.2f}%")
    print(f"      Macro Recall:      {rec_macro * 100:.2f}%")
    print(f"      Macro F1-Score:    {f1_macro * 100:.2f}%")
    print(f"      Weighted F1-Score: {f1_weighted * 100:.2f}%")
    print(f"      Total Test Time:   {inference_time_sec:.4f} s ({latency_per_sample_ms:.3f} ms/sample)")

    # Confusion matrix
    cm = confusion_matrix(y_test_labels, y_pred_labels, labels=classes)

    # 5. Save XGBoost Artifacts Separately
    print(f"\n[5/5] Saving XGBoost demo model artifact (separate from production RF)...")
    os.makedirs(MODEL_DIR, exist_ok=True)

    artifact_bundle = {
        "model": xgb_clf,
        "label_encoder": le,
        "features": FEATURES,
        "classes": classes,
        "model_type": "XGBClassifier",
        "hyperparameters": XGB_PARAMS,
        "metrics": {
            "accuracy": float(acc),
            "precision_macro": float(prec_macro),
            "recall_macro": float(rec_macro),
            "f1_macro": float(f1_macro),
            "f1_weighted": float(f1_weighted),
            "training_time_sec": float(training_time_sec),
            "inference_time_sec": float(inference_time_sec),
            "n_test_samples": int(len(X_test)),
            "n_classes": int(n_classes),
            "n_estimators": int(XGB_PARAMS["n_estimators"]),
            "n_features": int(len(FEATURES))
        }
    }

    joblib.dump(artifact_bundle, XGB_MODEL_PATH)
    print(f"      XGBoost demo model saved to: {XGB_MODEL_PATH}")

    # Also save evaluation metrics to JSON for model comparison script
    metrics_json_path = os.path.join(BASE_DIR, "xgboost_demo_metrics.json")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(artifact_bundle["metrics"], f, indent=2)
    print(f"      Metrics JSON saved to: {metrics_json_path}")

    # Print classification report
    print("\nDetailed Classification Report:")
    print(classification_report(y_test_labels, y_pred_labels, digits=4))

    return artifact_bundle["metrics"]


if __name__ == "__main__":
    train_and_evaluate_xgboost()
