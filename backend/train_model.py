"""
train_model.py
──────────────
Trains a RandomForestClassifier on the clean crop recommendation dataset
and saves to models/crop_model.pkl.
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(BASE_DIR)

CLEAN_DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")
RAW_DATA_PATH   = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation.csv")
DATA_PATH = CLEAN_DATA_PATH if os.path.exists(CLEAN_DATA_PATH) else RAW_DATA_PATH

MODEL_DIR  = os.path.join(ROOT_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "crop_model.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)

SOIL_TYPE_MAPPING = {
    "black": 0,
    "clay": 1,
    "loamy": 2,
    "red": 3,
    "sandy": 4,
}

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]
TARGET   = "label"


def train_crop_model(data_path=DATA_PATH, model_save_path=MODEL_PATH):
    print("=" * 60)
    print("  Crop Recommendation - ML Model Training (Baseline)")
    print("=" * 60)

    print(f"\n[1/4] Loading dataset: {data_path}")
    df = pd.read_csv(data_path)
    
    # If soil_type_encoded not already in file, ensure it's generated
    if "soil_type_encoded" not in df.columns:
        if "soil_type" in df.columns:
            df["soil_type_encoded"] = df["soil_type"].map(SOIL_TYPE_MAPPING).fillna(2).astype(int)
        else:
            raise ValueError("Dataset missing 'soil_type' or 'soil_type_encoded' column.")
            
    print(f"      Total Rows: {len(df)} | Unique Crops: {df[TARGET].nunique()}")
    print("      Soil type distribution:")
    if "soil_type" in df.columns:
        for s_name, count in df["soil_type"].value_counts().items():
            print(f"        - {s_name:8}: {count} rows")

    X = df[FEATURES].values
    y = df[TARGET].values

    print("\n[2/4] Splitting train/test (80/20 stratified split) ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"      Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    print("\n[3/4] Training RandomForestClassifier (200 trees, random_state=42) ...")
    model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    print(f"\n      [+] Overall Accuracy : {acc * 100:.2f}%")
    print(f"      [+] Macro Precision  : {prec_macro * 100:.2f}%")
    print(f"      [+] Macro Recall     : {rec_macro * 100:.2f}%")
    print(f"      [+] Macro F1-Score   : {f1_macro * 100:.2f}%")

    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    print(f"[4/4] Saving model -> {model_save_path}")
    joblib.dump(model, model_save_path)
    print("      [+] Model successfully saved.\n")
    return model, {
        "accuracy": acc,
        "precision_macro": prec_macro,
        "recall_macro": rec_macro,
        "f1_macro": f1_macro,
    }


if __name__ == "__main__":
    train_crop_model()
