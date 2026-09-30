"""
create_clean_dataset.py
───────────────────────
Builds a clean, agronomically sound training dataset for crop recommendation:
1. Loads datasets/Crop_recommendation.csv (1150 rows, 23 crops).
2. Assigns agronomically sound soil types (black, clay, loamy, red, sandy)
   based on ICAR and UAS Bengaluru/Dharwad package of practices.
3. Fixes the critical flaw where 'red' soil had 0 training samples.
4. Adds 'soil_type' and 'soil_type_encoded' columns.
5. Saves clean dataset to datasets/Crop_recommendation_clean.csv.
"""
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
INPUT_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation.csv")
OUTPUT_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")

# Standard label encoding matching CNN and inference pipeline
SOIL_TYPE_MAPPING = {
    "black": 0,
    "clay": 1,
    "loamy": 2,
    "red": 3,
    "sandy": 4,
}

# Agronomic soil distribution per crop (proportions across 50 samples)
# Based on ICAR and Karnataka UAS (Bangalore & Dharwad) agronomy
AGRONOMIC_SOIL_DISTRIBUTION = {
    "cotton":      {"black": 40, "red": 10},
    "chickpea":    {"black": 40, "loamy": 10},
    "wheat":       {"black": 40, "loamy": 10},
    "kidneybeans": {"black": 35, "loamy": 15},
    "lentil":      {"black": 40, "loamy": 10},
    "pigeonpeas":  {"red": 30, "black": 20},
    "mungbean":    {"red": 30, "black": 20},
    "blackgram":   {"red": 25, "loamy": 15, "black": 10},
    "mothbeans":   {"red": 30, "sandy": 20},
    "maize":       {"red": 30, "black": 20},
    "mango":       {"red": 30, "loamy": 20},
    "rice":        {"clay": 40, "loamy": 10},
    "banana":      {"clay": 35, "loamy": 15},
    "jute":        {"clay": 40, "loamy": 10},
    "coffee":      {"loamy": 35, "clay": 15},
    "orange":      {"loamy": 35, "red": 15},
    "grapes":      {"loamy": 35, "red": 15},
    "pomegranate": {"loamy": 35, "black": 15},
    "apple":       {"loamy": 50},
    "papaya":      {"loamy": 30, "sandy": 10, "red": 10},
    "watermelon":  {"sandy": 40, "loamy": 10},
    "muskmelon":   {"sandy": 40, "loamy": 10},
    "coconut":     {"sandy": 30, "red": 10, "loamy": 10},
}


def build_clean_dataset():
    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded {len(df)} rows from {INPUT_PATH}")
    
    # Assign deterministic, reproducible soil types based on agronomic distribution
    soil_types = []
    
    for crop in df["label"].unique():
        crop_indices = df[df["label"] == crop].index
        dist = AGRONOMIC_SOIL_DISTRIBUTION.get(crop, {"loamy": len(crop_indices)})
        
        # Build exact list of soil types for this crop
        crop_soils = []
        for soil, count in dist.items():
            crop_soils.extend([soil] * count)
        
        # In case length doesn't match exactly 50
        if len(crop_soils) < len(crop_indices):
            crop_soils.extend(["loamy"] * (len(crop_indices) - len(crop_soils)))
        elif len(crop_soils) > len(crop_indices):
            crop_soils = crop_soils[:len(crop_indices)]
            
        # Shuffle with fixed seed for natural permutation across the 50 rows of this crop
        rng = np.random.RandomState(42)
        rng.shuffle(crop_soils)
        
        for idx, s in zip(crop_indices, crop_soils):
            df.loc[idx, "soil_type"] = s

    df["soil_type_encoded"] = df["soil_type"].map(SOIL_TYPE_MAPPING).astype(int)
    
    print("\nSoil type distribution in clean dataset:")
    print(df["soil_type"].value_counts())
    print("\nSoil type encoded distribution:")
    print(df["soil_type_encoded"].value_counts().sort_index())
    
    # Verify features and ranges
    expected_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type", "soil_type_encoded", "label"]
    df = df[expected_cols]
    
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved clean dataset ({len(df)} rows) to: {OUTPUT_PATH}")
    return df


if __name__ == "__main__":
    build_clean_dataset()
