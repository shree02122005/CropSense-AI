import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLEAN_DATA_PATH = os.path.join(ROOT_DIR, "datasets", "Crop_recommendation_clean.csv")
MODEL_PATH = os.path.join(ROOT_DIR, "models", "crop_model.pkl")
AUDIT_DIR = os.path.join(ROOT_DIR, "research", "model_behavior_audit")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall", "soil_type_encoded"]
TARGET = "label"

def run_audit():
    print("=" * 80)
    print("CROP SENSE AI — PRODUCTION MODEL BEHAVIOR AUDIT")
    print("=" * 80)

    # -------------------------------------------------------------
    # PHASE 1: Canonical Training Dataset Inspection
    # -------------------------------------------------------------
    df = pd.read_csv(CLEAN_DATA_PATH)
    total_rows = len(df)
    unique_crops = sorted(df[TARGET].unique())
    num_classes = len(unique_crops)
    crop_counts = df[TARGET].value_counts().sort_index()

    print(f"\n[PHASE 1] CANONICAL TRAINING DATASET:")
    print(f"Total Rows: {total_rows}")
    print(f"Total Crop Classes: {num_classes}")
    print(f"Exact Crop Classes ({num_classes}): {unique_crops}")
    print(f"Min Samples per Crop: {crop_counts.min()} ({crop_counts.idxmin()})")
    print(f"Max Samples per Crop: {crop_counts.max()} ({crop_counts.idxmax()})")
    print(f"Is perfectly balanced? {crop_counts.min() == crop_counts.max()} (each class has {crop_counts.iloc[0]} samples)")

    # Save class_distribution.csv
    class_dist_df = pd.DataFrame({
        "crop": crop_counts.index,
        "sample_count": crop_counts.values,
        "percentage_of_dataset": (crop_counts.values / total_rows) * 100
    })
    class_dist_csv = os.path.join(AUDIT_DIR, "class_distribution.csv")
    class_dist_df.to_csv(class_dist_csv, index=False)
    print(f"Saved: {class_dist_csv}")

    # -------------------------------------------------------------
    # PHASE 2: Production Model Inspection
    # -------------------------------------------------------------
    model = joblib.load(MODEL_PATH)
    model_type = type(model).__name__
    model_classes = list(model.classes_)
    n_features = getattr(model, "n_features_in_", None)
    feat_names = getattr(model, "feature_names_in_", None)

    print(f"\n[PHASE 2] PRODUCTION MODEL (models/crop_model.pkl):")
    print(f"Model Type: {model_type}")
    print(f"Number of Estimators: {getattr(model, 'n_estimators', None)}")
    print(f"Number of Classes: {len(model_classes)}")
    print(f"Exact Model Classes: {model_classes}")
    print(f"Classes Match Dataset Classes Exactly: {model_classes == unique_crops}")
    print(f"Number of Input Features Expected: {n_features}")
    print(f"Feature Names in Model: {list(feat_names) if feat_names is not None else 'Not explicitly stored in pkl'}")

    # -------------------------------------------------------------
    # PHASE 3: Prediction Distribution Audit (Canonical Test Set)
    # -------------------------------------------------------------
    X = df[FEATURES].values
    y = df[TARGET].values

    # Stratified 80/20 train/test split matching train_model.py exactly
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    test_total = len(y_test)
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    acc = accuracy_score(y_test, y_pred)
    macro_p = precision_score(y_test, y_pred, average="macro", zero_division=0)
    macro_r = recall_score(y_test, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    # Actual vs Predicted distribution
    actual_series = pd.Series(y_test).value_counts().reindex(model_classes, fill_value=0)
    pred_series = pd.Series(y_pred).value_counts().reindex(model_classes, fill_value=0)

    # Per-class report
    clf_rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    pred_dist_rows = []
    for c in model_classes:
        rep_c = clf_rep.get(c, {})
        pred_dist_rows.append({
            "crop": c,
            "actual_test_count": int(actual_series[c]),
            "predicted_test_count": int(pred_series[c]),
            "predicted_percentage": round((pred_series[c] / test_total) * 100, 2),
            "precision": round(rep_c.get("precision", 0.0), 4),
            "recall": round(rep_c.get("recall", 0.0), 4),
            "f1_score": round(rep_c.get("f1-score", 0.0), 4),
            "support": int(rep_c.get("support", 0))
        })

    pred_dist_df = pd.DataFrame(pred_dist_rows).sort_values(by="predicted_test_count", ascending=False)
    pred_dist_csv = os.path.join(AUDIT_DIR, "prediction_distribution.csv")
    pred_dist_df.to_csv(pred_dist_csv, index=False)
    print(f"\n[PHASE 3] PREDICTION DISTRIBUTION (Test Set: {test_total} samples):")
    print(f"Overall Accuracy: {acc * 100:.2f}%")
    print(f"Macro Precision: {macro_p * 100:.2f}% | Recall: {macro_r * 100:.2f}% | F1: {macro_f1 * 100:.2f}%")
    print(f"Distinct Crops Actually Predicted on Test Set: {(pred_series > 0).sum()} / {len(model_classes)}")
    print(f"Saved: {pred_dist_csv}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=model_classes)
    cm_df = pd.DataFrame(cm, index=model_classes, columns=model_classes)
    cm_csv = os.path.join(AUDIT_DIR, "confusion_matrix.csv")
    cm_df.to_csv(cm_csv)
    print(f"Saved: {cm_csv}")

    # -------------------------------------------------------------
    # PHASE 4: Top-K Recommendations Analysis
    # -------------------------------------------------------------
    print(f"\n[PHASE 4] TOP-K RECOMMENDATIONS & CONFIDENCE:")
    top1_confs = []
    top2_confs = []
    top3_confs = []
    top5_confs = []

    for p in y_proba:
        sorted_p = np.sort(p)[::-1]
        top1_confs.append(sorted_p[0])
        top2_confs.append(sorted_p[1])
        top3_confs.append(sorted_p[2])
        top5_confs.append(sorted_p[4] if len(sorted_p) > 4 else 0.0)

    print(f"Mean Top-1 Confidence on Test Set: {np.mean(top1_confs) * 100:.2f}% (Min: {np.min(top1_confs)*100:.2f}%, Max: {np.max(top1_confs)*100:.2f}%)")
    print(f"Mean Top-2 Confidence on Test Set: {np.mean(top2_confs) * 100:.2f}%")
    print(f"Mean Top-3 Confidence on Test Set: {np.mean(top3_confs) * 100:.2f}%")
    print(f"Mean Top-5 Confidence on Test Set: {np.mean(top5_confs) * 100:.2f}%")

    # Sample top-k predictions
    sample_indices = [0, 10, 25, 50, 100]
    print("\nSample Test Instances Top-3 Predictions:")
    for idx in sample_indices:
        actual = y_test[idx]
        sorted_idx = np.argsort(y_proba[idx])[::-1]
        top3 = [(model_classes[i], round(y_proba[idx][i] * 100, 1)) for i in sorted_idx[:3]]
        print(f"  Sample #{idx:3d} (Actual: {actual:12}): Top-3 -> {top3}")

    # -------------------------------------------------------------
    # PHASE 6: Grapes Check
    # -------------------------------------------------------------
    grapes_actual = int(actual_series.get("grapes", 0))
    grapes_pred = int(pred_series.get("grapes", 0))
    grapes_pct = (grapes_pred / test_total) * 100
    grapes_rank = pred_dist_df["predicted_test_count"].rank(ascending=False, method="min").loc[pred_dist_df["crop"] == "grapes"].values[0]

    print(f"\n[PHASE 6] GRAPES SPECIFIC AUDIT:")
    print(f"A. Percentage of canonical test set predicted as Grapes: {grapes_pct:.2f}% ({grapes_pred} / {test_total})")
    print(f"B. Rank of Grapes in overall test prediction frequency: #{int(grapes_rank)}")
    print(f"C. Grapes Precision: {clf_rep['grapes']['precision']*100:.2f}% | Recall: {clf_rep['grapes']['recall']*100:.2f}% | F1: {clf_rep['grapes']['f1-score']*100:.2f}%")
    print(f"D. Is Grapes overrepresented on the canonical test set? {'YES' if grapes_pred > grapes_actual * 1.5 else 'NO'} (Actual: {grapes_actual}, Predicted: {grapes_pred})")

    # Now let's analyze WHY Grapes dominated in Karnataka lookup inputs
    # Let's inspect Grapes training distribution
    grapes_df = df[df[TARGET] == "grapes"]
    non_grapes_df = df[df[TARGET] != "grapes"]
    print("\nGrapes Nutrient Training Range vs Overall Dataset:")
    print(f"  Grapes N: [{grapes_df['N'].min():.1f}, {grapes_df['N'].max():.1f}] | Median: {grapes_df['N'].median():.1f}")
    print(f"  Grapes P: [{grapes_df['P'].min():.1f}, {grapes_df['P'].max():.1f}] | Median: {grapes_df['P'].median():.1f}")
    print(f"  Grapes K: [{grapes_df['K'].min():.1f}, {grapes_df['K'].max():.1f}] | Median: {grapes_df['K'].median():.1f}")
    print(f"  Overall Training K 90th percentile: {df['K'].quantile(0.90):.1f} kg/ha")
    print(f"  Crops with K > 100 kg/ha in entire dataset: {list(df[df['K'] > 100][TARGET].unique())}")

    # -------------------------------------------------------------
    # PHASE 7: Vegetable and Flower Taxonomy Check
    # -------------------------------------------------------------
    # Botanical / Agronomic classification of all 23 crops:
    # 23 classes: ['apple', 'banana', 'blackgram', 'chickpea', 'coconut', 'coffee', 'cotton',
    #              'grapes', 'jute', 'kidneybeans', 'lentil', 'maize', 'mango', 'mothbeans',
    #              'mungbean', 'muskmelon', 'orange', 'papaya', 'pigeonpeas', 'pomegranate',
    #              'rice', 'watermelon', 'wheat']
    print(f"\n[PHASE 7] TAXONOMY AUDIT (23 CROPS):")
    
    fruits = ["apple", "banana", "grapes", "mango", "muskmelon", "orange", "papaya", "pomegranate", "watermelon"]
    cereals = ["maize", "rice", "wheat"]
    pulses = ["blackgram", "chickpea", "kidneybeans", "lentil", "mothbeans", "mungbean", "pigeonpeas"]
    commercial_plantation = ["coconut", "coffee", "cotton", "jute"]
    vegetables = [] # NONE of traditional culinary vegetables (e.g. tomato, onion, potato, cabbage, brinjal, cauliflower, carrot)
    flowers = [] # NONE (e.g. rose, marigold, jasmine, chrysanthemum)

    print(f"Cereals ({len(cereals)}): {cereals}")
    print(f"Pulses / Legumes ({len(pulses)}): {pulses}")
    print(f"Fruits / Melons ({len(fruits)}): {fruits}")
    print(f"Commercial / Plantation / Fiber ({len(commercial_plantation)}): {commercial_plantation}")
    print(f"Vegetables ({len(vegetables)}): {vegetables} -> ZERO culinary vegetables present!")
    print(f"Flowers ({len(flowers)}): {flowers} -> ZERO floral crops present!")

    summary = {
        "num_classes": num_classes,
        "classes": unique_crops,
        "num_fruits": len(fruits),
        "fruits": fruits,
        "num_cereals": len(cereals),
        "cereals": cereals,
        "num_pulses": len(pulses),
        "pulses": pulses,
        "num_commercial": len(commercial_plantation),
        "commercial": commercial_plantation,
        "num_vegetables": len(vegetables),
        "num_flowers": len(flowers),
        "most_predicted_crop": pred_dist_df.iloc[0]["crop"],
        "most_predicted_count": int(pred_dist_df.iloc[0]["predicted_test_count"]),
        "most_predicted_pct": float(pred_dist_df.iloc[0]["predicted_percentage"]),
        "distinct_crops_predicted": int((pred_series > 0).sum()),
        "grapes_test_pct": float(grapes_pct),
        "grapes_test_count": int(grapes_pred),
        "grapes_rank": int(grapes_rank),
        "test_accuracy": float(acc)
    }

    with open(os.path.join(AUDIT_DIR, "audit_summary_stats.json"), "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    run_audit()
