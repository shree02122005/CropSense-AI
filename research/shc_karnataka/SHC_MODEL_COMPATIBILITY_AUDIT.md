# Soil Health Card (SHC) Model Compatibility Audit

**Candidate Evaluation Target**: `data/karnataka_main_places_npk_project_ready_v2.csv`  
**Reference Benchmark**: `data/karnataka_main_places_npk_project_ready_v1.csv` & `datasets/Crop_recommendation_clean.csv`  
**Production Model**: `models/crop_model.pkl` (8-feature Random Forest Classifier)  
**Location**: `research/shc_karnataka/SHC_MODEL_COMPATIBILITY_AUDIT.md`  
**Date**: October 2026  
**Auditor**: CropSense AI Research & Validation Pipeline  

---

## Executive Summary & Final Verdict

### Final Verdict:
### **2. SAFE ONLY WITH A CALIBRATION/COMPATIBILITY LAYER**

> [!CAUTION]
> **Summary Rationale**:
> While the new candidate file (`data/karnataka_main_places_npk_project_ready_v2.csv`) is grounded in real, government-published Karnataka Soil Health Card lab aggregates (2024–25 cycle) and fixes regional proxy inconsistencies from v1, **it CANNOT be deployed directly into production as a drop-in replacement**.
> 
> 1. **Extensive Out-of-Distribution (OOD) Shift**: **46.7% of Karnataka districts (14/30)** have Nitrogen values exceeding the maximum training boundary ($153.8\text{ kg/ha}$) of the production crop model. Furthermore, **36.7% of districts (11/30)** exceed the maximum Potassium boundary ($236.8\text{ kg/ha}$).
> 2. **Recommendation Churn**: When evaluated through the existing Random Forest model under controlled conditions, **23.3% of districts (7/30)** change their top crop recommendation (from grapes to coffee) with diluted model confidence (~19–20%).
> 3. **Requirements for Deployment**: The SHC values require a **calibration/compatibility layer** (such as quantile scaling or domain normalization into the crop model's feature space) before they can safely drive predictions without causing algorithmic extrapolation.

---

## Check A: Dataset Check

An inspection of `data/karnataka_main_places_npk_project_ready_v2.csv` was performed:

### 1. Row Count & District Coverage
- **Total Rows**: 31 entries (30 administrative districts + 1 statewide fallback row).
- **District Representation**: All 30 mapped administrative districts of Karnataka are present. (Note: Davanagere is omitted in both v1 and v2, and Ramanagara was retained as a regional proxy because it lacked a direct district code match in the 2024–25 portal extract).
- **Duplicate Rows**: **0 duplicate districts**.
- **Missing Values**: **0 missing / null values** across all 14 columns.

### 2. Source Fields and Provenance
- `shc_lab_aggregate` (29 districts): Aggregated village-level SHC sample counts from 2024–25 weighted by category midpoints.
- `regional_proxy` (1 district — Ramanagara): Unchanged from v1 (`N=249.7, P=46.8, K=180.4`).
- `shc_state_mean` (1 row — Karnataka coverage fallback): State mean of 31 district aggregates (`N=169.5, P=28.8, K=234.4`).
- `model_unit`: Explicitly marked as `kg/ha (available nutrient convention)`.

### 3. Numerical Summary: v2 Candidate vs. v1 Production
Statistics across the 30 administrative districts:

| Nutrient | Metric | Candidate v2 (SHC Lab Aggregate) | Production v1 (Published/Proxy) | Absolute Shift (v2 - v1) |
| :--- | :--- | :---: | :---: | :---: |
| **Available N** | Min / Max | **137.6 / 249.7 kg/ha** | 202.0 / 369.7 kg/ha | Min: -64.4, Max: -120.0 |
| | Mean ± Std | **170.0 ± 33.5 kg/ha** | 269.5 ± 74.4 kg/ha | **-99.5 kg/ha (-36.9%)** |
| | Median (IQR) | **151.1 (142.8–198.1) kg/ha** | 249.7 (203.6–369.7) kg/ha | -98.6 kg/ha |
| **Available P** | Min / Max | **16.2 / 46.8 kg/ha** | 9.2 / 75.0 kg/ha | Min: +7.0, Max: -28.2 |
| | Mean ± Std | **29.0 ± 7.6 kg/ha** | 26.3 ± 16.9 kg/ha | **+2.7 kg/ha (+10.3%)** |
| | Median (IQR) | **29.0 (23.7–34.6) kg/ha** | 24.9 (9.2–30.9) kg/ha | +4.1 kg/ha |
| **Available K** | Min / Max | **138.5 / 398.6 kg/ha** | 180.4 / 390.0 kg/ha | Min: -41.9, Max: +8.6 |
| | Mean ± Std | **231.8 ± 65.5 kg/ha** | 287.8 ± 66.8 kg/ha | **-56.0 kg/ha (-19.5%)** |
| | Median (IQR) | **225.8 (184.3–253.4) kg/ha** | 265.6 (265.6–346.4) kg/ha | -39.8 kg/ha |

---

## Check B: Model Compatibility

To determine whether the new SHC N/P/K values can be ingested safely by the crop model, we compared them directly against the empirical training distribution in `datasets/Crop_recommendation_clean.csv` (1,150 rows).

### Distribution Comparison: Training Data vs. v2 SHC

| Feature | Training Set Min | Training Set Mean | Training Set Median | Training Set Max | v2 SHC Range (Min–Max) | Districts Exceeding Training Max | % Out-of-Distribution (OOD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Nitrogen ($N$)** | 5.53 | 50.90 | 34.61 | **153.79 kg/ha** | 137.60 – 249.70 | **14 / 30 districts** | **46.7% ⚠️** |
| **Phosphorus ($P$)**| 3.30 | 51.65 | 48.52 | **177.91 kg/ha** | 16.20 – 46.80 | **0 / 30 districts** | **0.0%** |
| **Potassium ($K$)** | 3.54 | 48.85 | 34.08 | **236.77 kg/ha** | 138.50 – 398.60 | **11 / 30 districts** | **36.7% ⚠️** |

### Districts with Severe Out-of-Distribution Values:
1. **Nitrogen Exceedances ($N > 153.79\text{ kg/ha}$)**:
   - Ramanagara: $249.7\text{ kg/ha}$ (+62.4% above training ceiling)
   - Koppal: $227.4\text{ kg/ha}$ (+47.9%)
   - Hassan: $222.4\text{ kg/ha}$ (+44.6%)
   - Chamarajanagar: $220.8\text{ kg/ha}$ (+43.6%)
   - Kodagu: $211.8\text{ kg/ha}$ (+37.7%)
   - Dharwad: $209.0\text{ kg/ha}$ (+35.9%)
   - Gadag: $208.4\text{ kg/ha}$ (+35.5%)
   - Ballari: $200.3\text{ kg/ha}$ (+30.2%)
   - Haveri: $191.6\text{ kg/ha}$ (+24.6%)
   - Vijayanagara: $178.0\text{ kg/ha}$ (+15.7%)
   - Bidar: $177.8\text{ kg/ha}$ (+15.6%)
   - Bagalkot: $171.5\text{ kg/ha}$ (+11.5%)
   - Udupi: $169.3\text{ kg/ha}$ (+10.1%)
   - Shivamogga: $155.8\text{ kg/ha}$ (+1.3%)
2. **Potassium Exceedances ($K > 236.77\text{ kg/ha}$)**:
   - Kalaburagi: $398.6\text{ kg/ha}$ (+68.3% above training ceiling)
   - Bidar: $396.5\text{ kg/ha}$ (+67.5%)
   - Yadgir: $373.5\text{ kg/ha}$ (+57.7%)
   - Koppal: $287.8\text{ kg/ha}$ (+21.5%)
   - Dharwad: $268.0\text{ kg/ha}$ (+13.2%)
   - Shivamogga: $265.6\text{ kg/ha}$ (+12.2%)
   - Gadag: $254.1\text{ kg/ha}$ (+7.3%)
   - Chikkamagaluru: $253.7\text{ kg/ha}$ (+7.1%)
   - Mysuru: $252.5\text{ kg/ha}$ (+6.6%)
   - Vijayapura: $251.2\text{ kg/ha}$ (+6.1%)
   - Kodagu: $250.6\text{ kg/ha}$ (+5.8%)

### Compatibility Diagnosis:
The crop model was trained on an international agricultural benchmark where median Nitrogen is $34.6\text{ kg/ha}$ and median Potassium is $34.1\text{ kg/ha}$. In contrast, actual Karnataka soils have median Available Nitrogen of $151.1\text{ kg/ha}$ and Potassium of $225.8\text{ kg/ha}$. Without an explicit normalization or calibration layer, the Random Forest model is forced to evaluate inputs at the extreme boundaries of its leaf nodes, leading to unpredictable probability distributions.

---

## Check C & D: Prediction Shadow Test & Comparison with Production

A controlled shadow test was executed across all 30 Karnataka districts using the existing production model (`models/crop_model.pkl`).
- **Controlled Environmental Parameters**: Standard Karnataka seasonal baseline conditions (`temp = 26.0°C`, `humidity = 68.0%`, `ph = 6.5`, `rainfall = 120.0mm`, `soil_type_encoded = 3` [Red soil]).
- **Input Comparison**: Vector 1 used production v1 inputs; Vector 2 used candidate v2 inputs.

### Summary Metrics:
- **Fertility Category Shifts**: **23 out of 30 districts (76.7%)** changed their N/P/K classification between v1 and v2.
- **Top-1 Crop Recommendation Shifts**: **7 out of 30 districts (23.3%)** changed their recommended crop.
- **Crop Inversion Pattern**: In all 7 shifting districts, the recommended crop shifted from **grapes** to **coffee**.
- **Model Confidence**: Confidence in shifted districts remained clustered between **19.0% and 20.5%**, reflecting low certainty across the 23 candidate classes.

### Districts Where Crop Recommendations Changed:
1. **Bengaluru Urban**: `grapes` (20.0%) $\rightarrow$ `coffee` (20.0%) [$\Delta N = -107.6, \Delta P = -19.9, \Delta K = +3.7$]
2. **Kodagu**: `grapes` (20.5%) $\rightarrow$ `coffee` (20.5%) [$\Delta N = -157.9, \Delta P = +19.6, \Delta K = -15.0$]
3. **Dakshina Kannada**: `grapes` (20.5%) $\rightarrow$ `coffee` (19.0%) [$\Delta N = -229.6, \Delta P = +13.2, \Delta K = -127.1$]
4. **Udupi**: `grapes` (20.5%) $\rightarrow$ `coffee` (20.0%) [$\Delta N = -200.4, \Delta P = +18.2, \Delta K = -92.7$]
5. **Uttara Kannada**: `grapes` (20.5%) $\rightarrow$ `coffee` (20.0%) [$\Delta N = -217.6, \Delta P = +15.4, \Delta K = -71.6$]
6. **Ballari**: `grapes` (21.0%) $\rightarrow$ `coffee` (19.0%) [$\Delta N = -3.3, \Delta P = -7.5, \Delta K = -161.6$]
7. **Vijayanagara**: `grapes` (21.0%) $\rightarrow$ `coffee` (20.0%) [$\Delta N = -25.6, \Delta P = -5.7, \Delta K = -186.0$]

*(The complete 30-district row-by-row dataset is saved in [`research/shc_karnataka/shc_vs_production_comparison.csv`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_karnataka/shc_vs_production_comparison.csv)).*

---

## Check E: Detailed Verdict Explanation

### Verdict: **2. SAFE ONLY WITH A CALIBRATION/COMPATIBILITY LAYER**

#### Why Not 1 (Safe to Use Directly)?
Direct substitution would inject values exceeding the training maximum for 46.7% of Nitrogen entries and 36.7% of Potassium entries. Because tree-based models like Random Forests do not extrapolate linear trends beyond their training extrema (they predict constant plateau values at boundary leaves), the model loses discriminatory power when nearly half the state falls outside its training box.

#### Why Not 3 (Not Safe to Use for the Current Model)?
`karnataka_main_places_npk_project_ready_v2.csv` represents **authentic, government-verified Soil Health Card lab aggregate data** from 692,142 soil samples. It successfully remedies the severe regional proxy distortion identified in v1 (where Mysuru and Mandya were erroneously assigned Hassan's wetland profile). The data itself is sound and valuable; the limitation lies strictly in the **scale mismatch** between Indian soil test values and the crop model's synthetic training dataset.

#### What a Calibration Layer Must Do:
To deploy v2 safely:
1. **Quantile / Min-Max Mapping**: Map the SHC empirical distribution $[137.6, 249.7]$ into the crop model's effective Nitrogen sensitivity window $[20.0, 120.0\text{ kg/ha}]$.
2. **Domain Adaptation**: Map high Potassium values ($>236\text{ kg/ha}$) to the model's upper quantile boundary ($180\text{--}220\text{ kg/ha}$) so high-K soils register as optimal for potassium-demanding crops without falling off the edge of the feature space.
3. **Alternative**: Retrain the crop model on an expanded agronomic dataset that incorporates genuine Indian Soil Health Card ranges.

---

## Production Safety Verification Statement

We confirm that **NO PRODUCTION FILES WERE MODIFIED**:
- `backend/npk_lookup.py`: **UNCHANGED**
- `backend/predict_api.py`: **UNCHANGED**
- `backend/main.py`: **UNCHANGED**
- `backend/train_model.py`: **UNCHANGED**
- `models/crop_model.pkl`: **UNCHANGED**
- `datasets/Crop_recommendation_clean.csv`: **UNCHANGED**
- `data/karnataka_main_places_npk_project_ready_v1.csv`: **UNCHANGED**
- `frontend/`: **UNCHANGED**

All validation scripts, comparison tables, and audit documentation are strictly isolated under `research/shc_karnataka/`.
