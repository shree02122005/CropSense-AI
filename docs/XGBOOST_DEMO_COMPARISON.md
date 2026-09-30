# CropSense AI — XGBoost Academic Demonstration & Model Comparison

**Date:** September 2026  
**Document Version:** 1.0 (Academic Demonstration & Benchmarking)  
**Author:** CropSense AI Research & Development  
**Status:** Completed & Verified  

> [!IMPORTANT]
> **Statement on Production Architecture:**  
> **"The XGBoost model was created as an experimental comparison model. The deployed CropSense AI application continues to use the validated Random Forest model."**  
> Under no circumstances is the production prediction pipeline (`models/crop_model.pkl`, `backend/predict_api.py`, `backend/main.py`) altered or replaced.

---

## 1. Objective

The objective of this investigation is to provide an empirical, reproducible, and academically rigorous benchmark comparing an **XGBoost Classifier (`xgboost.XGBClassifier`)** against the existing, validated **Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)** for agricultural crop recommendation.

This comparison provides external evaluators, examiners, and project stakeholders with:
1. A fair, identical-split baseline comparison using the exact same 8 input features and holdout test samples.
2. Transparent trade-offs in accuracy, macro/weighted F1-scores, training latency, inference throughput, and memory footprint.
3. Agronomic and operational justification for maintaining Random Forest as the production engine.

---

## 2. Dataset Information

- **Dataset File:** `datasets/Crop_recommendation_clean.csv`
- **Total Records:** 1,150 observations
- **Target Classes:** 23 distinct crop classes (`apple`, `banana`, `blackgram`, `chickpea`, `coconut`, `coffee`, `cotton`, `grapes`, `jute`, `kidneybeans`, `lentil`, `maize`, `mango`, `mothbeans`, `mungbean`, `muskmelon`, `orange`, `papaya`, `pigeonpeas`, `pomegranate`, `rice`, `watermelon`, `wheat`).
- **Class Balance:** Perfectly balanced — exactly **50 observations per class**.
- **Data Integrity:** 0 missing values, verified no NaN/null values across all columns.
- **Data Provenance:** Clean Phase 5 dataset containing genuine Karnataka soil associations and climate ranges without artificial multipliers or synthetic augmentations.

---

## 3. Features Used

The model uses the exact identical 8-dimensional agronomic feature vector defined in Phase 5 and Phase 6:

| Index | Feature Name | Physical Unit | Agronomic Description | Physical Range |
|:---:|:---|:---:|:---|:---:|
| 0 | `N` | kg/ha | Soil available Nitrogen | 5.53 – 153.79 |
| 1 | `P` | kg/ha | Soil available Phosphorus | 3.30 – 177.91 |
| 2 | `K` | kg/ha | Soil available Potassium | 3.54 – 236.77 |
| 3 | `temperature` | °C | Ambient mean temperature | 11.54 – 40.50 |
| 4 | `humidity` | % | Relative atmospheric humidity | 1.76 – 100.00 |
| 5 | `ph` | Dimensionless (0–14) | Soil pH (acidity / alkalinity) | 4.90 – 7.76 |
| 6 | `rainfall` | mm | Mean seasonal precipitation | 7.39 – 315.58 |
| 7 | `soil_type_encoded` | Ordinal int (0–4) | Soil texture: 0=black, 1=clay, 2=loamy, 3=red, 4=sandy | 0 – 4 |

---

## 4. Train/Test Methodology

To guarantee strict scientific comparability and avoid data leakage:
1. **Split Protocol:** Stratified 80/20 train/test split.
   - **Training Set:** 920 samples (80.0%, exactly 40 samples per class).
   - **Holdout Test Set:** 230 samples (20.0%, exactly 10 samples per class).
2. **Reproducibility Seed:** `random_state = 42` (identical to the Phase 6 Random Forest baseline).
3. **Data Leakage Check:** Disjoint partition verification confirmed $\text{Train} \cap \text{Test} = \emptyset$ (0 overlapping sample indices).
4. **Target Encoding:** 
   - Random Forest natively processes string targets.
   - XGBoost uses `sklearn.preprocessing.LabelEncoder` mapping the 23 classes to integers $[0..22]$. An inverse transform maps predictions back to crop names.

---

## 5. Model Configurations

### 5.1 Random Forest (Production Baseline)
```python
RandomForestClassifier(
    n_estimators=200,
    criterion='gini',
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    bootstrap=True,
    random_state=42,
    n_jobs=-1
)
```

### 5.2 XGBoost (Academic Demonstration)
```python
XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    subsample=0.9,
    colsample_bytree=0.9,
    random_state=42,
    eval_metric='mlogloss',
    n_jobs=-1
)
```

---

## 6. Empirical Evaluation Results

Both models were evaluated on the identical 230-sample holdout test set.

### 6.1 Random Forest Measured Metrics (Production Model)
- **Accuracy:** **93.04%** (214/230 correct predictions)
- **Macro-Averaged Precision:** **93.22%**
- **Macro-Averaged Recall:** **93.04%**
- **Macro-Averaged F1-Score:** **93.00%**
- **Weighted F1-Score:** **93.00%**
- **Training Time:** ~0.450 seconds
- **Inference Latency:** 0.275 ms / sample (63.2 ms for 230 test samples)
- **Model File Size:** 12.90 MB (`crop_model.pkl`)

### 6.2 XGBoost Measured Metrics (Academic Demo Model)
- **Accuracy:** **90.87%** (209/230 correct predictions)
- **Macro-Averaged Precision:** **91.21%**
- **Macro-Averaged Recall:** **90.87%**
- **Macro-Averaged F1-Score:** **90.76%**
- **Weighted F1-Score:** **90.76%**
- **Training Time:** 1.3986 seconds
- **Inference Latency:** 0.034 ms / sample (7.8 ms for 230 test samples)
- **Model File Size:** 2.07 MB (`crop_model_xgboost_demo.pkl`)

---

## 7. Side-by-Side Comparison Table

| Metric / Characteristic | Random Forest (Production) | XGBoost (Academic Demo) | Empirical Difference |
|:---|:---:|:---:|:---:|
| **Overall Test Accuracy** | **93.04%** | 90.87% | **+2.17% (RF higher)** |
| **Macro Precision** | **93.22%** | 91.21% | **+2.01% (RF higher)** |
| **Macro Recall** | **93.04%** | 90.87% | **+2.17% (RF higher)** |
| **Macro F1-Score** | **93.00%** | 90.76% | **+2.24% (RF higher)** |
| **Weighted F1-Score** | **93.00%** | 90.76% | **+2.24% (RF higher)** |
| **Correct Predictions (Test 230)** | **214 / 230** | 209 / 230 | **+5 correct predictions** |
| **Training Duration** | **0.450 s** | 1.399 s | RF trains 3.1× faster |
| **Inference Latency (per query)** | 0.275 ms | **0.034 ms** | XGBoost 8.1× faster inference |
| **Model Disk Size** | 12.90 MB | **2.07 MB** | XGBoost 6.2× more compact |
| **Number of Estimators / Rounds** | 200 trees | 100 boosting rounds | — |
| **Target Representation** | Native string labels | Encoded ordinal (0..22) | — |
| **Operational Role** | **Active Production Deployed** | **Academic Comparison Only** | — |

---

## 8. Detailed Observations

1. **Classification Accuracy & F1-Score:**
   - Random Forest achieved an overall accuracy of **93.04%** vs. **90.87%** for XGBoost (+2.17% advantage for Random Forest).
   - Macro F1 is **93.00%** for Random Forest vs. **90.76%** for XGBoost.
   - On this tabular agricultural dataset of 1,150 samples across 23 classes, Random Forest's bootstrap bagging with 200 fully grown decision trees provides superior variance reduction and handles overlapping ecological envelopes with slightly greater fidelity than gradient boosted shallow trees (depth 4).

2. **Per-Class Breakdown:**
   - Both models achieve 100% precision and recall on distinctive crops like `coconut`, `blackgram`, `cotton`, and `mango`.
   - The primary misclassifications for both models occur among closely related pulse legumes (`mothbeans`, `mungbean`) and cereals (`maize`, `wheat`), where soil and rainfall envelopes naturally overlap. Random Forest correctly classified 5 more borderline cases than XGBoost.

3. **Inference Latency & Model Size:**
   - XGBoost demonstrated significantly faster inference latency (0.034 ms/sample vs. 0.275 ms/sample) and a much smaller model footprint (2.07 MB vs. 12.90 MB).
   - In a web application where total API latency is dominated by remote network calls to OpenWeather (150–350 ms) and SoilGrids (200–500 ms), the 0.24 ms difference in ML inference has negligible impact on end-user perception.

4. **Training Speed:**
   - Random Forest trained in ~0.45 seconds on 8 parallel CPU workers, whereas sequential gradient boosting took ~1.40 seconds. Both are comfortably within interactive execution thresholds.

---

## 9. Why Random Forest Remains the Production Model

1. **Higher Empirical Accuracy & F1:**  
   Random Forest delivers **93.04% accuracy** compared to **90.87%** for XGBoost on the verified holdout split.
2. **Probability Calibration for Crop Diversity:**  
   CropSense AI presents the **top-3 ranked crop candidates** with indicative probabilities. Random Forest's forest-wide vote averaging provides well-behaved, smooth probability distributions across 23 classes without severe overconfidence.
3. **Out-of-Distribution Robustness:**  
   Decision trees in Random Forest create piecewise constant partitions bounded by min/max leaf thresholds, which prevents extreme gradient runaway when out-of-distribution soil conditions (e.g. high Karnataka potassium/nitrogen values) are evaluated.
4. **Zero Pipeline Disruption:**  
   The deployed system has undergone end-to-end integration and stability testing (Phase 8–10) around `models/crop_model.pkl`. Maintaining Random Forest avoids introducing unnecessary risks or schema transformations to production endpoints.

---

## 10. Limitations

1. **Dataset Size:**  
   With 1,150 samples (50 per class), gradient boosting methods (XGBoost) do not have the massive sample volumes where their sequential residual learning typically outpaces bagging ensembles.
2. **Hyperparameter Scope:**  
   XGBoost was trained using a standard, reproducible academic configuration (`n_estimators=100`, `max_depth=4`, `learning_rate=0.1`). Extensive hyperparameter grid searching or Bayesian optimization was deliberately avoided to preserve an honest, transparent comparison against default Random Forest parameters.
3. **OOD Generalization:**  
   Both models remain limited by the bounding box of the training dataset features. While Random Forest achieved 93.04% on the holdout split, neither model can reliably extrapolate far outside its training range without flagging Out-of-Distribution (OOD) warnings.
