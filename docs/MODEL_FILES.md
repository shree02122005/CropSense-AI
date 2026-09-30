# CropSense AI — Model Files Documentation

This document describes all machine learning and deep learning models contained in the `models/` directory, detailing their architecture, role, file format, and evaluation metrics.

---

## 1. Summary of Model Artifacts

| Model File | Size | Role | Algorithm / Framework | Key Evaluation Metric |
|:---|:---:|:---:|:---|:---:|
| `models/crop_model.pkl` | 13.52 MB | **Production Deployed** | Random Forest Classifier (`sklearn`) | **93.04% Accuracy**, 93.00% F1 |
| `models/crop_model_xgboost_demo.pkl` | 2.17 MB | **Academic Demo Only** | XGBoost Classifier (`xgboost`) | **90.87% Accuracy**, 90.76% F1 |
| `models/soil_cnn_model.keras` | 13.98 MB | **Production Deployed** | MobileNetV2 Transfer Learning (`tf.keras`) | 5 soil classes, ~80% top-1 |
| `models/soil_cnn_model.h5` | 13.76 MB | **Multi-tier Fallback** | MobileNetV2 Weights / H5 | Fallback for legacy TF/Keras |
| `models/soil_cnn_model.pkl` | 287 KB | **Lightweight Fallback** | Color / Texture Centroid Classifier | CPU / low-memory fallback |

---

## 2. Production Crop Recommendation Model

- **File Path:** `models/crop_model.pkl`
- **Algorithm:** `sklearn.ensemble.RandomForestClassifier`
- **Hyperparameters:**
  - `n_estimators`: 200
  - `criterion`: `'gini'`
  - `max_depth`: `None` (fully grown decision trees)
  - `min_samples_split`: 2
  - `min_samples_leaf`: 1
  - `bootstrap`: `True`
  - `random_state`: 42
  - `n_jobs`: -1
- **Feature Vector (8 features, strict order):**
  `[N, P, K, temperature, humidity, ph, rainfall, soil_type_encoded]`
- **Target:** 23 distinct crop classes
- **Performance (Holdout Test Split, n=230):**
  - Accuracy: **93.04%** (214/230 correct)
  - Macro Precision: **93.22%**
  - Macro Recall: **93.04%**
  - Macro F1-Score: **93.00%**
  - Weighted F1-Score: **93.00%**
- **Inference Latency:** 0.275 ms / sample
- **Why Active in Production:** Bagging over 200 trees delivers superior stability, resistance to leaf-level outliers, and well-calibrated class probability distributions across candidate crops.

---

## 3. Academic Demonstration XGBoost Model

- **File Path:** `models/crop_model_xgboost_demo.pkl`
- **Algorithm:** `xgboost.XGBClassifier`
- **Role:** Standalone academic comparison model for examiner presentation and performance benchmarking.
- **Hyperparameters:**
  - `n_estimators`: 100
  - `max_depth`: 4
  - `learning_rate`: 0.1
  - `subsample`: 0.9
  - `colsample_bytree`: 0.9
  - `random_state`: 42
  - `eval_metric`: `'mlogloss'`
- **Performance (Holdout Test Split, n=230):**
  - Accuracy: **90.87%** (209/230 correct)
  - Macro Precision: **91.21%**
  - Macro Recall: **90.87%**
  - Macro F1-Score: **90.76%**
  - Weighted F1-Score: **90.76%**
- **Inference Latency:** 0.034 ms / sample
- **Packaging:** Serialized dictionary containing the trained model, `LabelEncoder`, feature column list, classes, and evaluation metadata.
- **Note:** Decoupled from production; does NOT power the live API.

---

## 4. Soil Classification CNN Models

- **Architecture:** Pre-trained MobileNetV2 base (ImageNet weights, frozen) + GlobalAveragePooling2D + Dense(256, ReLU) + BatchNormalization + Dropout(0.5) + Dense(128, ReLU) + Dropout(0.3) + Dense(5, Softmax).
- **Target Classes (5):** `black`, `clay`, `loamy`, `red`, `sandy`
- **Input Dimensions:** 224 × 224 × 3 normalized RGB image tensor
- **Multi-Tier Loading Strategy:**
  1. `soil_cnn_model.keras` (Native Keras v3 format, preferred for TensorFlow 2.16+).
  2. `soil_cnn_model.h5` (HDF5 format, loaded if `.keras` is unavailable).
  3. `soil_cnn_model.pkl` (Scikit-learn / color-histogram fallback if TensorFlow is absent).
- **Domain Rejection & Heuristics:**
  Integrated with Laplacian variance blur detection (`variance < 50.0`), extreme lighting filters (darkness < 20, brightness > 245), and color centroid verification to prevent out-of-domain images from producing spurious classifications.
