import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLEAN_DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")
PROD_MODEL_PATH = os.path.join(ROOT_DIR, "models", "crop_model.pkl")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]
TARGET = "label"

def run_baseline_experiment():
    print("=" * 70)
    print("PHASE 2 — REPRODUCE PRODUCTION BASELINE EXPERIMENT")
    print("=" * 70)

    # 1. Load data
    df = pd.read_csv(CLEAN_DATA_PATH)
    print(f"Loaded dataset: {CLEAN_DATA_PATH} ({len(df)} rows, {len(df[TARGET].unique())} classes)")

    X = df[FEATURES].values
    y = df[TARGET].values

    # 2. Train/Test split identical to production train_model.py
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Train set: {len(X_train)} samples | Test set: {len(X_test)} samples")

    # 3. Train RandomForest
    t0_train = time.perf_counter()
    baseline_rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    baseline_rf.fit(X_train, y_train)
    t1_train = time.perf_counter()
    train_time_sec = t1_train - t0_train

    # 4. Inference timing on test set
    t0_infer = time.perf_counter()
    y_pred = baseline_rf.predict(X_test)
    y_proba = baseline_rf.predict_proba(X_test)
    t1_infer = time.perf_counter()
    total_infer_time_sec = t1_infer - t0_infer
    per_sample_infer_ms = (total_infer_time_sec / len(X_test)) * 1000.0

    # 5. Metrics calculation
    acc = accuracy_score(y_test, y_pred)
    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    prec_weighted = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    rec_weighted = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    cm = confusion_matrix(y_test, y_pred, labels=baseline_rf.classes_)
    feat_importances = dict(zip(FEATURES, [round(float(imp), 4) for imp in baseline_rf.feature_importances_]))

    print(f"\nBaseline Metrics:")
    print(f"  Accuracy           : {acc * 100:.2f}%")
    print(f"  Macro Precision    : {prec_macro * 100:.2f}%")
    print(f"  Weighted Precision : {prec_weighted * 100:.2f}%")
    print(f"  Macro Recall       : {rec_macro * 100:.2f}%")
    print(f"  Weighted Recall    : {rec_weighted * 100:.2f}%")
    print(f"  Macro F1-Score     : {f1_macro * 100:.2f}%")
    print(f"  Weighted F1-Score  : {f1_weighted * 100:.2f}%")
    print(f"  Training Time      : {train_time_sec:.4f} seconds")
    print(f"  Test Inference Time: {total_infer_time_sec:.4f} seconds ({per_sample_infer_ms:.4f} ms/sample)")
    print(f"\nFeature Importances:")
    for feat, imp in sorted(feat_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  {feat:18}: {imp:.4f} ({imp*100:.2f}%)")

    # Verify against production model file
    prod_model = joblib.load(PROD_MODEL_PATH)
    y_pred_prod = prod_model.predict(X_test)
    prod_acc = accuracy_score(y_test, y_pred_prod)
    print(f"\nDirect Production Model Verification:")
    print(f"  Production Model Test Accuracy: {prod_acc * 100:.2f}%")
    print(f"  Identical predictions match   : {(y_pred == y_pred_prod).mean() * 100:.2f}%")

    results = {
        "model_name": "Production Baseline RandomForestClassifier (200 trees, random_state=42)",
        "accuracy": float(acc),
        "precision_macro": float(prec_macro),
        "precision_weighted": float(prec_weighted),
        "recall_macro": float(rec_macro),
        "recall_weighted": float(rec_weighted),
        "f1_macro": float(f1_macro),
        "f1_weighted": float(f1_weighted),
        "train_time_sec": float(train_time_sec),
        "total_infer_time_sec": float(total_infer_time_sec),
        "per_sample_infer_ms": float(per_sample_infer_ms),
        "feature_importances": feat_importances,
        "classes": list(baseline_rf.classes_),
        "confusion_matrix": cm.tolist()
    }

    out_json = os.path.join(os.path.dirname(__file__), "baseline_experiment_results.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved results to: {out_json}")

if __name__ == "__main__":
    run_baseline_experiment()
