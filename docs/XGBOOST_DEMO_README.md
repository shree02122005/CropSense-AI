# CropSense AI — XGBoost Academic Demo & Comparison Guide

This document outlines the exact, reproducible commands to train the standalone XGBoost comparison model, execute the side-by-side benchmark comparison, and view the results.

> [!IMPORTANT]
> **Production Protection Reminder:**  
> The deployed CropSense AI application continues to use the validated **Random Forest model (`models/crop_model.pkl`)**.  
> The XGBoost scripts are strictly decoupled and do NOT alter production prediction endpoints or models.

---

## 1. Quick Verification & Execution Commands

All commands should be executed from the project root or the `backend/` directory using the project's Python virtual environment (`.venv`).

### Command 1: Train the XGBoost Demonstration Model
Trains the standalone XGBoost classifier on the exact same Phase 5 dataset (`datasets/Crop_recommendation_clean.csv`) with the identical 80/20 stratified split (`random_state=42`) and saves the model to `models/crop_model_xgboost_demo.pkl`:

```powershell
# From the project root:
.\.venv\Scripts\python.exe backend/train_xgboost_demo.py
```

Or from within the `backend/` folder:
```powershell
cd backend
..\.venv\Scripts\python.exe train_xgboost_demo.py
```

### Command 2: Run the Model Comparison Benchmark
Compares the existing production Random Forest (`models/crop_model.pkl`) and the demo XGBoost model (`models/crop_model_xgboost_demo.pkl`) on the 230 holdout test samples:

```powershell
# From the project root:
.\.venv\Scripts\python.exe backend/compare_models.py
```

Or from within the `backend/` folder:
```powershell
cd backend
..\.venv\Scripts\python.exe compare_models.py
```

---

## 2. Viewing the Results

### Terminal Output
Running `compare_models.py` displays a clean side-by-side comparison table:

```
--------------------------------------------------------------------------------
Metric / Characteristic          | Random Forest (Production) | XGBoost (Demo)      
--------------------------------------------------------------------------------
Overall Test Accuracy            |                   93.04% |              90.87%
Macro-Averaged Precision         |                   93.22% |              91.21%
Macro-Averaged Recall            |                   93.04% |              90.87%
Macro-Averaged F1-Score          |                   93.00% |              90.76%
Weighted F1-Score                |                   93.00% |              90.76%
Training Duration                |                  0.4500s |             1.3986s
Inference Time (230 samples)     |                  0.0632s |             0.0078s
Inference Latency (per sample)   |                 0.275 ms |            0.034 ms
Model Artifact File Size         |                 12.90 MB |             2.07 MB
Number of Estimators / Rounds    |                      200 |                 100
Deployment Status                |      Active (Production) |  Academic Demo Only
--------------------------------------------------------------------------------
```

### Generated Files & Artifacts

1. **Complete Documentation Report:**
   - [`XGBOOST_DEMO_COMPARISON.md`](./XGBOOST_DEMO_COMPARISON.md): Detailed 12-section technical comparison covering methodology, metrics, confusion matrices, latency, and agronomic rationale.

2. **Benchmarking Chart:**
   - [`XGBOOST_RF_COMPARISON.png`](./XGBOOST_RF_COMPARISON.png): Side-by-side bar chart showing measured Accuracy, Macro Precision, Macro Recall, and Macro F1 across both models without visual exaggeration.

3. **Machine-Readable Benchmark Data:**
   - [`backend/model_comparison_results.json`](./backend/model_comparison_results.json): Structured JSON output containing all empirical performance metrics for programmatic access.
   - [`backend/xgboost_demo_metrics.json`](./backend/xgboost_demo_metrics.json): XGBoost test metrics.

4. **Model Artifacts:**
   - Production Model (Untouched): [`models/crop_model.pkl`](./models/crop_model.pkl)
   - Academic Demo Model: [`models/crop_model_xgboost_demo.pkl`](./models/crop_model_xgboost_demo.pkl)

5. **Safety Backup:**
   - [`BACKUP_XGBOOST_DEMO/`](./BACKUP_XGBOOST_DEMO/): Backup of production `crop_model.pkl`, `predict_api.py`, and `main.py`.

---

## 3. Production Safety Guarantee

- **FastAPI Endpoint (`POST /predict`):** Continues serving recommendations using the validated Random Forest model (`models/crop_model.pkl`).
- **Frontend Application:** Continues communicating with the production backend without any modifications or disruptions.
- **Zero Risk:** The XGBoost scripts run in complete isolation and cannot overwrite or destabilize the deployed system.
