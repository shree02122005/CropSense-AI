import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
df = pd.read_csv(os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv"))

print("=== OVERALL TRAINING DATA STATS ===")
print(df[["N", "P", "K"]].describe().T[["mean", "std", "min", "25%", "50%", "75%", "max"]])

print("\n=== PER-CROP MEDIAN N, P, K ===")
crop_grp = df.groupby("label")[["N", "P", "K"]].median()
print(crop_grp)

print("\n=== HIGH N CROPS (> 100 kg/ha) ===")
print(crop_grp[crop_grp["N"] > 100])

print("\n=== LOW N CROPS (< 40 kg/ha) ===")
print(crop_grp[crop_grp["N"] < 40])

print("\n=== HIGH K CROPS (> 100 kg/ha) ===")
print(crop_grp[crop_grp["K"] > 100])
