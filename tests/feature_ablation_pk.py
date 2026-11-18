"""
feature_ablation_pk.py
──────────────────────
Controlled feature-ablation experiment on the CropSense AI crop recommendation model.
Measures the empirical predictive contribution of Phosphorus (P) and Potassium (K)
on the canonical dataset (Crop_recommendation_clean.csv).

PROTOCOL:
- Model: RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
- Dataset: datasets/Crop_recommendation_clean.csv (1150 samples, 23 classes)
- Train/Test Split: 80/20 Stratified (random_state=42)
- Zero modification to production model, pipeline, dataset, or prediction API.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.inspection import permutation_importance

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
ASSETS_DIR = os.path.join(DOCS_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

TARGET = "label"
ALL_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]

EXPERIMENTS = {
    "Baseline": {
        "features": ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"],
        "removed": "None",
        "description": "Full 8-feature production specification"
    },
    "Without P": {
        "features": ["N", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"],
        "removed": "P only",
        "description": "7 features (Phosphorus ablated)"
    },
    "Without K": {
        "features": ["N", "P", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"],
        "removed": "K only",
        "description": "7 features (Potassium ablated)"
    },
    "Without P & K": {
        "features": ["N", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"],
        "removed": "P & K",
        "description": "6 features (Phosphorus and Potassium ablated)"
    },
}

def run_ablation():
    print("=" * 80)
    print("  CONTROLLED FEATURE ABLATION EXPERIMENT: P & K CONTRIBUTION ANALYSIS")
    print("=" * 80)

    # 1. Load data
    df = pd.read_csv(DATA_PATH)
    print(f"\n[+] Loaded canonical dataset: {DATA_PATH}")
    print(f"    Total samples: {len(df)} | Unique crops: {df[TARGET].nunique()}")
    
    # 2. Replicate exact stratified split
    indices = np.arange(len(df))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.2, random_state=42, stratify=df[TARGET]
    )
    df_train = df.iloc[train_idx]
    df_test = df.iloc[test_idx]

    y_train = df_train[TARGET].values
    y_test = df_test[TARGET].values

    print(f"[+] Replicated 80/20 stratified split (seed=42):")
    print(f"    Train size: {len(y_train)} | Test size: {len(y_test)}")
    assert len(y_test) == 230, f"Expected 230 test samples, got {len(y_test)}"

    results = {}
    models = {}

    for exp_name, exp_cfg in EXPERIMENTS.items():
        feat_list = exp_cfg["features"]
        X_train = df_train[feat_list].values
        X_test = df_test[feat_list].values

        rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        models[exp_name] = rf

        y_pred = rf.predict(X_test)
        correct = int((y_pred == y_test).sum())
        total = int(len(y_test))
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))

        results[exp_name] = {
            "features": feat_list,
            "features_removed": exp_cfg["removed"],
            "description": exp_cfg["description"],
            "correct_predictions": correct,
            "total_test_samples": total,
            "accuracy": acc,
            "macro_precision": prec,
            "macro_recall": rec,
            "macro_f1": f1,
        }

        print(f"\n--- {exp_name.upper()} ({len(feat_list)} features) ---")
        print(f"    Features: {feat_list}")
        print(f"    Accuracy:        {acc * 100:.2f}% ({correct}/{total})")
        print(f"    Macro Precision: {prec * 100:.2f}%")
        print(f"    Macro Recall:    {rec * 100:.2f}%")
        print(f"    Macro F1:        {f1 * 100:.2f}%")

    # Baseline comparison metrics
    base_acc = results["Baseline"]["accuracy"]
    base_prec = results["Baseline"]["macro_precision"]
    base_rec = results["Baseline"]["macro_recall"]
    base_f1 = results["Baseline"]["macro_f1"]

    for exp_name in results:
        results[exp_name]["delta_accuracy_pp"] = round((results[exp_name]["accuracy"] - base_acc) * 100, 2)
        results[exp_name]["delta_precision_pp"] = round((results[exp_name]["macro_precision"] - base_prec) * 100, 2)
        results[exp_name]["delta_recall_pp"] = round((results[exp_name]["macro_recall"] - base_rec) * 100, 2)
        results[exp_name]["delta_f1_pp"] = round((results[exp_name]["macro_f1"] - base_f1) * 100, 2)

    # Feature Importance for Baseline (Gini MDI)
    base_rf = models["Baseline"]
    gini_importances = base_rf.feature_importances_
    base_feats = EXPERIMENTS["Baseline"]["features"]

    sorted_gini_idx = np.argsort(gini_importances)[::-1]
    feature_importance_list = []
    print("\n" + "=" * 60)
    print("  BASELINE FEATURE IMPORTANCE (Gini Impurity / MDI)")
    print("=" * 60)
    for rank, idx in enumerate(sorted_gini_idx, 1):
        f_name = base_feats[idx]
        imp = float(gini_importances[idx])
        pct = imp * 100
        feature_importance_list.append({
            "rank": rank,
            "feature": f_name,
            "importance": round(imp, 4),
            "percentage": round(pct, 2)
        })
        marker = " <--- FOCUS" if f_name in ["N", "P", "K"] else ""
        print(f"  {rank}. {f_name:18}: {imp:.4f} ({pct:.2f}%){marker}")

    # Permutation Importance on held-out test set
    print("\n[+] Calculating Permutation Importance on held-out test set (n_repeats=10, seed=42) ...")
    X_test_base = df_test[base_feats].values
    perm_res = permutation_importance(
        base_rf, X_test_base, y_test, n_repeats=10, random_state=42, n_jobs=-1
    )
    sorted_perm_idx = np.argsort(perm_res.importances_mean)[::-1]
    perm_importance_list = []
    print("\n" + "=" * 60)
    print("  BASELINE PERMUTATION IMPORTANCE (Test Set Decrease in Accuracy)")
    print("=" * 60)
    for rank, idx in enumerate(sorted_perm_idx, 1):
        f_name = base_feats[idx]
        p_mean = float(perm_res.importances_mean[idx])
        p_std = float(perm_res.importances_std[idx])
        perm_importance_list.append({
            "rank": rank,
            "feature": f_name,
            "mean_decrease": round(p_mean, 4),
            "std": round(p_std, 4),
            "mean_decrease_pp": round(p_mean * 100, 2)
        })
        marker = " <--- FOCUS" if f_name in ["N", "P", "K"] else ""
        print(f"  {rank}. {f_name:18}: {p_mean:.4f} +/- {p_std:.4f} (delta acc: {p_mean*100:+.2f} pp){marker}")

    # Save numerical JSON
    output_data = {
        "experiment_timestamp": pd.Timestamp.now().isoformat(),
        "dataset": "Crop_recommendation_clean.csv",
        "sample_count": len(df),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "results": results,
        "gini_feature_importances": feature_importance_list,
        "permutation_importances": perm_importance_list
    }
    json_path = os.path.join(DOCS_DIR, "p_k_feature_ablation_results.json")
    with open(json_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n[+] Saved numerical results to: {json_path}")

    # Generate Visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Model Accuracy Comparison
    names = list(results.keys())
    accs = [results[k]["accuracy"] * 100 for k in names]
    colors = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444"]
    
    bars = axes[0].bar(names, accs, color=colors, width=0.55, edgecolor="#1f2937", linewidth=1.2)
    axes[0].set_ylim(80, 100)
    axes[0].set_ylabel("Holdout Test Accuracy (%)", fontsize=12, fontweight="bold")
    axes[0].set_title("Ablation Study: Crop Recommendation Accuracy", fontsize=13, fontweight="bold", pad=12)
    axes[0].grid(axis="y", linestyle="--", alpha=0.5)

    for bar, acc, name in zip(bars, accs, names):
        delta = results[name]["delta_accuracy_pp"]
        delta_str = f" ({delta:+.2f} pp)" if delta != 0 else " (Baseline)"
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            f"{acc:.2f}%{delta_str}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

    # Plot 2: Feature Importance (Gini vs Permutation)
    feat_names = [item["feature"] for item in feature_importance_list]
    gini_scores = [item["percentage"] for item in feature_importance_list]
    
    # Highlight N, P, K with distinct colors
    bar_colors = ["#f97316" if f in ["P", "K"] else "#10b981" if f == "N" else "#64748b" for f in feat_names]
    
    y_pos = np.arange(len(feat_names))
    axes[1].barh(y_pos, gini_scores, color=bar_colors, edgecolor="#1f2937", linewidth=1)
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels(feat_names, fontsize=11, fontweight="bold")
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Mean Decrease in Impurity / Gini Importance (%)", fontsize=12, fontweight="bold")
    axes[1].set_title("Baseline Feature Importance (N, P, K Highlighted)", fontsize=13, fontweight="bold", pad=12)
    axes[1].grid(axis="x", linestyle="--", alpha=0.5)

    for idx, (score, f) in enumerate(zip(gini_scores, feat_names)):
        axes[1].text(score + 0.3, idx, f"{score:.2f}%", va="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plot_path = os.path.join(ASSETS_DIR, "P_K_FEATURE_ABLATION.png")
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[+] Saved visualization to: {plot_path}")

    return output_data

if __name__ == "__main__":
    run_ablation()
