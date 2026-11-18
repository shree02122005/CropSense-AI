# CropSense AI — Production Model Behavior & Architectural Audit

**Document**: Production Crop Recommendation System Audit  
**Location**: `research/model_behavior_audit/PRODUCTION_MODEL_BEHAVIOR_AUDIT.md`  
**Date**: October 2026  
**Auditor**: CropSense AI Independent Verification & Validation Pipeline  
**Production Integrity**: READ-ONLY AUDIT — **ZERO PRODUCTION FILES MODIFIED**  

---

## Executive Summary

This audit rigorously inspects and documents the empirical behavior, taxonomy, feature pipeline, and prediction distributions of the CURRENT production CropSense AI system.

The primary motivation of this audit was to investigate whether the system exhibits genuine algorithmic bias (specifically regarding recurring recommendations of `Grapes`), verify the taxonomic coverage of the model (vegetables, fruits, flowers, cereals, pulses), and evaluate the end-to-end data construction flow in the production API.

### Core Discoveries at a Glance:
1. **Model Is Well-Balanced on Canonical Data**: When evaluated on the canonical test set (230 samples, 80/20 stratified split), the production Random Forest achieves **93.04% accuracy** (Macro F1: **93.00%**) and predicts **all 23 out of 23 crops**.
2. **Grapes Does NOT Dominate on Test Set**: `Grapes` accounts for only **3.91% of predictions (9 / 230 samples)** on the test set, ranking **#19 out of 23 crops**. The model has 100% precision and 90% recall for Grapes on canonical inputs.
3. **The Grapes Phenomenon is an Out-of-Distribution Input Artifact**: Grapes only dominated in Karnataka lookup shadow tests because the regional lookup files (`v1` and `v2`) supply bulk soil Potassium values ($K \in [180, 398]\text{ kg/ha}$) that exceed the growth requirements of 21 out of 23 crops in the training dataset. In the training dataset, only `apple` and `grapes` have $K > 100\text{ kg/ha}$, and temperatures in Karnataka rule out cold-temperate apples.
4. **Zero Culinary Vegetables or Flowers Exist in the Dataset**: The dataset contains **0 vegetables** (no tomato, onion, potato, brinjal, cabbage, etc.) and **0 flower crops** (no marigold, rose, jasmine, etc.). The model literally cannot recommend crops it was never trained to predict.
5. **Production Files Intact**: No production code, models, or data files were altered.

---

## Phase 1 — Canonical Training Dataset Audit

**File Inspected**: `datasets/Crop_recommendation_clean.csv`

### 1. Dataset Dimensions & Balance
- **Total Rows**: 1,150 rows
- **Total Crop Classes**: 23 distinct classes
- **Samples per Crop**: Exactly **50 samples** per crop (Min: 50, Max: 50). The dataset is perfectly balanced across all 23 classes ($23 \times 50 = 1,150$).
- *Associated CSV*: [research/model_behavior_audit/class_distribution.csv](file:///c:/Users/shree/Downloads/major-project-demo1/research/model_behavior_audit/class_distribution.csv)

### 2. Exact Crop Class Inventory (23 Classes)
```
apple, banana, blackgram, chickpea, coconut, coffee, cotton, grapes, jute, kidneybeans, lentil, maize, mango, mothbeans, mungbean, muskmelon, orange, papaya, pigeonpeas, pomegranate, rice, watermelon, wheat
```

### 3. Agronomic Taxonomy & Crop Category Breakdown
- **Cereals (3 crops)**: `maize`, `rice`, `wheat`
- **Pulses / Legumes (7 crops)**: `blackgram`, `chickpea`, `kidneybeans`, `lentil`, `mothbeans`, `mungbean`, `pigeonpeas`
- **Fruits & Horticultural Melons (9 crops)**: `apple`, `banana`, `grapes`, `mango`, `muskmelon`, `orange`, `papaya`, `pomegranate`, `watermelon`
- **Commercial / Plantation / Fiber (4 crops)**: `coconut`, `coffee`, `cotton`, `jute`
- **Culinary Vegetables (0 crops)**: **NONE**. Traditional market vegetables such as tomato, onion, potato, brinjal/eggplant, cauliflower, cabbage, okra/ladyfinger, green chili, spinach, and carrot are completely absent from the training dataset. *(Note: muskmelon and watermelon are botanical pepo fruits / cucurbit melons).*
- **Flower / Floricultural Crops (0 crops)**: **NONE**. Floricultural crops like marigold, rose, jasmine, and chrysanthemum are completely absent.

---

## Phase 2 — Production Model Architecture

**File Inspected**: `models/crop_model.pkl`

- **Model Class**: `sklearn.ensemble._forest.RandomForestClassifier`
- **Number of Estimators**: 200 trees (`n_estimators=200`, `random_state=42`)
- **Number of Input Features**: 8 features
- **Exact Input Feature Order Expected**:
  1. `N` (Available Nitrogen, kg/ha)
  2. `P` (Available Phosphorus, kg/ha)
  3. `K` (Available Potassium, kg/ha)
  4. `temperature` (Ambient Temperature, °C)
  5. `humidity` (Relative Humidity, %)
  6. `ph` (Soil pH, standard scale)
  7. `rainfall` (Precipitation, mm)
  8. `soil_type_encoded` (Categorical integer: `black=0, clay=1, loamy=2, red=3, sandy=4`)
- **Number of Target Classes**: 23 classes
- **Exact Model Classes Match Training Dataset**: **YES (100% exact match in alphabetical order)**.

---

## Phase 3 — Prediction Distribution Audit

**Evaluation Protocol**: Stratified 80/20 train/test split matching `backend/train_model.py` (`random_state=42`, $N_{train}=920, N_{test}=230$).  
*Associated CSVs*:
- [research/model_behavior_audit/prediction_distribution.csv](file:///c:/Users/shree/Downloads/major-project-demo1/research/model_behavior_audit/prediction_distribution.csv)
- [research/model_behavior_audit/confusion_matrix.csv](file:///c:/Users/shree/Downloads/major-project-demo1/research/model_behavior_audit/confusion_matrix.csv)

### 1. Global Performance Metrics
- **Overall Test Accuracy**: **93.04%** (214 correct out of 230 test samples)
- **Macro Precision**: **93.22%**
- **Macro Recall**: **93.04%**
- **Macro F1-Score**: **93.00%**
- **Distinct Crops Predicted**: **23 out of 23** (every crop is predicted at least 8 times).

### 2. Complete Test Set Prediction Distribution (230 Samples)

| Crop | Actual Test Count | Predicted Test Count | Predicted % | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **apple** | 10 | 11 | 4.78% | 0.9091 | 1.0000 | 0.9524 | 10 |
| **cotton** | 10 | 11 | 4.78% | 0.9091 | 1.0000 | 0.9524 | 10 |
| **kidneybeans** | 10 | 11 | 4.78% | 0.9091 | 1.0000 | 0.9524 | 10 |
| **watermelon** | 10 | 11 | 4.78% | 0.9091 | 1.0000 | 0.9524 | 10 |
| **mungbean** | 10 | 11 | 4.78% | 0.7273 | 0.8000 | 0.7619 | 10 |
| **maize** | 10 | 11 | 4.78% | 0.7273 | 0.8000 | 0.7619 | 10 |
| **blackgram** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **rice** | 10 | 10 | 4.35% | 0.9000 | 0.9000 | 0.9000 | 10 |
| **pomegranate**| 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **chickpea** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **coconut** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **mango** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **lentil** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **orange** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **jute** | 10 | 10 | 4.35% | 0.9000 | 0.9000 | 0.9000 | 10 |
| **wheat** | 10 | 10 | 4.35% | 0.8000 | 0.8000 | 0.8000 | 10 |
| **papaya** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **pigeonpeas** | 10 | 10 | 4.35% | 1.0000 | 1.0000 | 1.0000 | 10 |
| **banana** | 10 | 9 | 3.91% | 1.0000 | 0.9000 | 0.9474 | 10 |
| **coffee** | 10 | 9 | 3.91% | 1.0000 | 0.9000 | 0.9474 | 10 |
| **grapes** | 10 | 9 | 3.91% | 1.0000 | 0.9000 | 0.9474 | 10 |
| **muskmelon** | 10 | 9 | 3.91% | 1.0000 | 0.9000 | 0.9474 | 10 |
| **mothbeans** | 10 | 8 | 3.48% | 0.7500 | 0.6000 | 0.6667 | 10 |

> [!NOTE]
> The prediction distribution across the canonical test set is exceptionally even. The highest predicted frequency is 11 counts (4.78%), and the lowest is 8 counts (3.48%).

---

## Phase 4 — Top-K Recommendations & Confidence Distribution

### 1. Model & API Top-K Capabilities
- The Random Forest model outputs class probabilities via `predict_proba`.
- In `backend/predict_api.py`, `_predict_crops` extracts the top 3 ranked crops:
  ```python
  proba = model.predict_proba(feat)[0]
  top3 = np.argsort(proba)[::-1][:3]
  return [(model.classes_[i], float(proba[i])) for i in top3]
  ```
- The API returns all 3 ranked crops with confidence scores.
- The frontend (`ResultPage.js` and `CropComparisonDashboard.js`) natively consumes and renders these ranked cards.

### 2. Confidence Metrics on In-Distribution Test Set
- **Mean Top-1 Confidence**: **77.60%** (Min: 22.50%, Max: 100.00%)
- **Mean Top-2 Confidence**: **12.39%**
- **Mean Top-3 Confidence**: **3.83%**
- **Mean Top-5 Confidence**: **1.28%**

When valid, in-distribution agronomic values are fed to the model, it makes decisive, high-confidence primary predictions (~78%) with a distinct runner-up (~12%).

---

## Phase 5 — Live API Flow & Feature Construction

**File Inspected**: `backend/predict_api.py`

### Step-by-Step Feature Construction Trace:
```
[User GPS (lat, lon) + Soil Image]
        │
        ├──► CNN Model (cnn/predict_soil.py)
        │      └─► soil_type (e.g., 'red') ──► SOIL_TYPE_LABELS mapping ──► soil_type_encoded (3)
        │
        ├──► OpenWeather API (api.openweathermap.org)
        │      ├─► Temperature (°C)
        │      ├─► Humidity (%)
        │      └─► Rainfall (mm) [Defaults to 0.0 mm if no active rain; fallback if API fails]
        │
        ├──► ISRIC SoilGrids 2.0 API (rest.isric.org)
        │      ├─► phh2o (0-5cm mean) ──► normalized by /10.0 if >10 ──► pH (e.g., 6.5)
        │      └─► soc (0-5cm mean) ──► normalized by /100.0 ──► Organic Carbon
        │
        └──► Regional NPK Lookup (backend/npk_lookup.py)
               └─► Haversine nearest reference place in data/karnataka_main_places_npk_project_ready_v1.csv
                     ├─► N (kg/ha)
                     ├─► P (kg/ha)
                     └─► K (kg/ha)
                               │
                               ▼
        ┌────────────────────────────────────────────────────────┐
        │ Out-of-Distribution (OOD) Detector                     │
        │ detect_out_of_distribution_features(...)               │
        │ Transparently detects whether N,P,K exceed bounds.     │
        │ Does NOT clamp, mutate, or reject input values.        │
        └──────────────────────┬─────────────────────────────────┘
                               │
                               ▼
        ┌────────────────────────────────────────────────────────┐
        │ Random Forest Inference                                │
        │ feat = [N, P, K, temp, humidity, ph, rain, soil_code]  │
        │ model.predict_proba(feat)                              │
        │ Top-3 ranked crops with confidence + metadata returned │
        └────────────────────────────────────────────────────────┘
```

### Transformations, Defaults, and Clamping Verification:
1. **Soil Type**: Clamped/mapped via `{"black": 0, "clay": 1, "loamy": 2, "red": 3, "sandy": 4}`. Defaults to `loamy` (2) if unrecognized.
2. **Weather Fallbacks**: If OpenWeather is unavailable, latitudinal fallbacks are applied ($\text{lat} \le 23^\circ \rightarrow \text{temp}=27, \text{humidity}=70, \text{rain}=120$).
3. **SoilGrids Fallbacks**: If SoilGrids returns null (urban/coastal coordinates), latitudinal fallback is applied ($\text{lat} \le 23^\circ \rightarrow \text{pH}=5.8, \text{soc}=2.5$).
4. **NPK Lookup**: If coordinate distance calculation fails, statewide default profile is used ($N=249.7, P=46.8, K=180.4$).
5. **No Manipulation of ML Features**: Raw values from weather, SoilGrids, and NPK lookup are passed **directly and unmanipulated** into `_predict_crops`. No artificial multipliers or diversity boosts are applied.

---

## Phase 6 — Grapes Investigation: Evidence & Root Cause

### 1. Empirical Findings on Canonical Data
- **Test set prediction percentage**: **3.91%** (9 out of 230 predictions).
- **Ground truth test set percentage**: **4.35%** (10 out of 230 samples).
- **Test set rank**: **#19 out of 23 crops**.
- **Is Grapes dominant in the model?**: **NO.** On valid data, Grapes behaves with exemplary precision (100.0%) and normal recall (90.0%).

### 2. Why Did Grapes Dominate in Karnataka Lookup Tests?
In shadow testing against the Karnataka lookup tables (`v1` and `v2`), Grapes was recommended in **100% of districts under v1** and **76.7% of districts under v2**.

**The Technical Root Cause**:
1. In the canonical training dataset, Potassium ($K$) across all crops has a median of $34.1\text{ kg/ha}$ and a 90th percentile of $85.4\text{ kg/ha}$.
2. The ONLY crops in the training dataset that require $K > 100\text{ kg/ha}$ are:
   - `grapes` (median $K = 204.7\text{ kg/ha}$, range $[156.4, 228.1]$)
   - `apple` (median $K = 197.7\text{ kg/ha}$, range $[150.3, 222.0]$)
   - (All other 21 crops thrive on $K < 85\text{ kg/ha}$).
3. However, standard Karnataka agricultural soils contain high extractable Potassium ($K \in [180.4, 398.6]\text{ kg/ha}$).
4. When `backend/npk_lookup.py` passes $K \ge 180.4\text{ kg/ha}$ into the Random Forest:
   - The tree decision thresholds immediately branch into the high-K leaf nodes ($K > 140$).
   - Within that branch, only `apple` and `grapes` exist.
   - Temperature splits ($T > 22^\circ\text{C}$) immediately eliminate cold-climate `apple`.
   - **Result**: The trees are forced into predicting `grapes`.
5. **Conclusion**: Grapes dominance is **NOT an internal model bug or skewed class prior**; it is an **Out-of-Distribution input mismatch** caused by feeding regional soil potassium reserves ($K > 180\text{ kg/ha}$) into a model trained on crop demand values ($K < 85\text{ kg/ha}$ for non-fruit crops).

---

## Phase 7 — Vegetable & Flower Crop Assessment

### 1. Vegetable Status
- Are culinary market vegetables present in the model? **NO.**
- The dataset does not contain tomato, onion, potato, cabbage, cauliflower, brinjal/eggplant, carrot, okra, beans, or spinach.
- **Agronomic consequence**: The CropSense AI model **cannot recommend vegetables** under any circumstances because it was never trained on them.

### 2. Flower Status
- Are floricultural crops present in the model? **NO.**
- The dataset does not contain marigold, rose, jasmine, chrysanthemum, or crossandra.
- **Agronomic consequence**: The CropSense AI model **cannot recommend flowers** under any circumstances.

---

## Phase 8 — Final Verified Findings

| Audit Question | Verified Finding |
| :--- | :--- |
| **1. Number of crop classes** | **23** |
| **2. Exact crop classes** | `apple, banana, blackgram, chickpea, coconut, coffee, cotton, grapes, jute, kidneybeans, lentil, maize, mango, mothbeans, mungbean, muskmelon, orange, papaya, pigeonpeas, pomegranate, rice, watermelon, wheat` |
| **3. Number of vegetables** | **0** (Zero culinary vegetables) |
| **4. Number of fruits** | **9** (`apple`, `banana`, `grapes`, `mango`, `muskmelon`, `orange`, `papaya`, `pomegranate`, `watermelon`) |
| **5. Number of flowers** | **0** (Zero floral crops) |
| **6. Most frequently predicted crop (Test Set)** | **Tied (apple, cotton, kidneybeans, watermelon, mungbean, maize)** |
| **7. Percentage predicted as that crop** | **4.78%** (11 out of 230 test samples) |
| **8. Number of distinct crops actually predicted** | **23 / 23 crops (100% of all classes)** |
| **9. Is Grapes genuinely dominating?** | **NO** (Only 3.91% on test set, Rank #19. Dominance in API is purely an OOD high-K input artifact) |
| **10. Are vegetables present in the model?** | **NO** |
| **11. Are flowers present in the model?** | **NO** |
| **12. Does current API return multiple ranked recommendations?** | **YES** (Returns Top-3 ranked crops with individual confidence probabilities) |
| **13. Any bug or suspicious transformation found?** | **NO** (Pipeline is clean, deterministic, and preserves raw values; root issue is training data semantic scope) |
| **14. Production files modified?** | **NO** (100% untouched) |

---

## Production Files Untouched Verification

All production files remain strictly intact and unchanged:
- `models/crop_model.pkl` : **UNTOUCHED**
- `datasets/Crop_recommendation_clean.csv` : **UNTOUCHED**
- `backend/predict_api.py` : **UNTOUCHED**
- `backend/main.py` : **UNTOUCHED**
- `backend/npk_lookup.py` : **UNTOUCHED**
- `data/karnataka_main_places_npk_project_ready_v1.csv` : **UNTOUCHED**
- `frontend/` : **UNTOUCHED**
