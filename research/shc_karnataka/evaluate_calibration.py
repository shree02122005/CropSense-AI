import os
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V1_PATH = os.path.join(ROOT_DIR, "data", "karnataka_main_places_npk_project_ready_v1.csv")
V2_PATH = os.path.join(ROOT_DIR, "data", "karnataka_main_places_npk_project_ready_v2.csv")
CROP_DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")

df_v1 = pd.read_csv(V1_PATH)
df_v2 = pd.read_csv(V2_PATH)
df_crop = pd.read_csv(CROP_DATA_PATH)

# Identify the 4 anchor points in v1
anchors = ["Bengaluru Urban", "Hassan", "Dharwad", "Raichur"]
v1_anchors = df_v1[df_v1["district"].isin(anchors)].set_index("district")
v2_anchors = df_v2[df_v2["district"].isin(anchors)].set_index("district")

print("=== APPROACH B: OVERLAPPING REFERENCE ANCHORS (N=4) ===")
print("\nAnchor Values Comparison:")
comp_df = pd.DataFrame({
    "v1_N": v1_anchors["N_model_input"],
    "v2_N": v2_anchors["N_model_input"],
    "v1_P": v1_anchors["P_model_input"],
    "v2_P": v2_anchors["P_model_input"],
    "v1_K": v1_anchors["K_model_input"],
    "v2_K": v2_anchors["K_model_input"],
})
print(comp_df)

print("\nCorrelations across the 4 anchors:")
for nut in ["N", "P", "K"]:
    x = comp_df[f"v1_{nut}"].values
    y = comp_df[f"v2_{nut}"].values
    r, p_val = pearsonr(x, y)
    rho, p_rho = spearmanr(x, y)
    print(f"  Nutrient {nut}: Pearson r = {r:.4f} (p = {p_val:.4f}), Spearman rho = {rho:.4f} (p = {p_rho:.4f})")

print("\n=== APPROACH C: CANONICAL TRAINING CORRELATION vs SHC ===")
print("Training data N-P correlation:", df_crop[["N", "P", "K"]].corr())
print("SHC v2 district N-P correlation:", df_v2[df_v2["district"] != "Karnataka coverage"][["N_model_input", "P_model_input", "K_model_input"]].corr())
