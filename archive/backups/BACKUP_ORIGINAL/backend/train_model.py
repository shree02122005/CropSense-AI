"""
train_model.py
──────────────
Trains a RandomForestClassifier on Crop_recommendation.csv and saves to models/crop_model.pkl
"""
import os, sys
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(BASE_DIR)
DATA_PATH  = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation.csv")
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

CROP_TO_SOIL_TYPE = {
    "cotton": "black",
    "maize": "black",
    "wheat": "black",
    "sorghum": "black",
    "chickpea": "black",
    "lentil": "black",
    "pigeonpeas": "black",
    "blackgram": "black",
    "mungbean": "black",
    "kidneybeans": "black",
    "mothbeans": "black",
    "soybean": "black",
    "rice": "clay",
    "banana": "clay",
    "papaya": "clay",
    "orange": "clay",
    "coffee": "clay",
    "pepper": "clay",
    "cardamom": "clay",
    "arecanut": "clay",
    "apple": "loamy",
    "pomegranate": "loamy",
    "grapes": "loamy",
    "tomato": "loamy",
    "potato": "loamy",
    "vegetables": "loamy",
    "watermelon": "sandy",
    "muskmelon": "sandy",
    "groundnut": "sandy",
    "sunflower": "sandy",
    "onion": "sandy",
}

DEFAULT_SOIL_TYPE = "loamy"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]
TARGET   = "label"

print("=" * 50)
print("  Crop Recommendation – ML Model Training")
print("=" * 50)

print(f"\n[1/4] Loading dataset: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
df["soil_type"] = df[TARGET].map(CROP_TO_SOIL_TYPE).fillna(DEFAULT_SOIL_TYPE)
df["soil_type_encoded"] = df["soil_type"].map(SOIL_TYPE_MAPPING).astype(int)
print(f"      Rows: {len(df)}  |  Classes: {df[TARGET].nunique()}  |  Soil types: {df['soil_type'].nunique()}")
print(f"      Soil type distribution: {df['soil_type'].value_counts().to_dict()}")

X = df[FEATURES].values
y = df[TARGET].values

print("[2/4] Splitting train/test (80/20) …")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("[3/4] Training RandomForestClassifier (200 trees) …")
model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"\n      ✔ Accuracy: {acc * 100:.2f}%")
print("\n" + classification_report(y_test, y_pred))

print(f"[4/4] Saving model → {MODEL_PATH}")
joblib.dump(model, MODEL_PATH)
print("      ✔ Model saved successfully.\n")
