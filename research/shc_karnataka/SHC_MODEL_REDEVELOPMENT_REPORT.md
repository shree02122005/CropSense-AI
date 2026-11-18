# Karnataka Soil Health Card (SHC) Model Redevelopment & Compatibility Report

**Project**: CropSense AI — Soil Nutrient Modeling & Crop Recommendation Pipeline  
**Document**: Research & Experimental Model Redevelopment Report  
**Location**: `research/shc_karnataka/SHC_MODEL_REDEVELOPMENT_REPORT.md`  
**Date**: October 2026  
**Auditor**: CropSense AI Research & Validation Pipeline  
**Status**: Experimental Validation Complete — **FINAL DECISION: D. SHC DATA IS NOT CURRENTLY SUITABLE FOR PRODUCTION**  

---

## Executive Summary

This report delivers the complete experimental investigation into upgrading CropSense AI's N/P/K data pipeline using the corrected Karnataka Soil Health Card (SHC) district-level dataset (`data/karnataka_shc_npk_district.csv` / `data/karnataka_main_places_npk_project_ready_v2.csv`).

The core objective was to determine whether a scientifically defensible crop recommendation model or calibration layer can be built using the new district-level SHC N/P/K information instead of the existing regional proxy lookup (`data/karnataka_main_places_npk_project_ready_v1.csv`).

### Definitive Conclusion:
**The Karnataka SHC dataset CANNOT be used to train or directly drive CropSense AI's crop recommendation model in production at this time.**

```
+---------------------------------------------------------------------------------------------------+
| FINAL RECOMMENDATION:                                                                             |
| D. SHC DATA IS NOT CURRENTLY SUITABLE FOR PRODUCTION                                              |
+---------------------------------------------------------------------------------------------------+
| 1. Current Production Accuracy     : 93.04%                                                       |
| 2. Experimental Model Accuracy     : 92.61% (Quantile Benchmark; suffers boundary saturation)    |
| 3. Scientific Feasibility of Calib : NO (Statistically underdetermined & semantic category error)|
| 4. SHC Impact on Crop Model        : SEVERELY WORSENED (63.3% OOD, severe confidence dilution)   |
| 5. Number of Districts Tested      : 30 administrative districts                                  |
| 6. Recommendations Changed         : 7 / 30 districts (23.3% churn; flips grapes -> coffee)       |
| 7. Out-of-Distribution (OOD) Rate  : 63.3% of districts (46.7% N > max, 36.7% K > max)            |
| 8. Production Assets Untouched     : 100% UNTOUCHED (models/crop_model.pkl, backend, frontend)   |
+---------------------------------------------------------------------------------------------------+
```

---

## Phase 1 — Comprehensive Inspection & Semantic Audit

A rigorous multi-file audit was conducted across all relevant production and experimental assets:

### 1. File Inspection Manifest
1. `datasets/Crop_recommendation_clean.csv`: Canonical training dataset (1,150 rows, 23 crops, 8 features).
2. `models/crop_model.pkl`: Production Random Forest classifier (200 trees, 8 input features, 23 classes).
3. `backend/train_model.py`: Model training script implementing an 80/20 stratified split with `random_state=42`.
4. `backend/npk_lookup.py`: Haversine spatial lookup mapping user coordinates to nearest reference location.
5. `backend/predict_api.py`: Multi-modal inference pipeline (CNN soil type, OpenWeather, SoilGrids, Random Forest).
6. `data/karnataka_main_places_npk_project_ready_v1.csv`: Current production lookup table (31 rows).
7. `data/karnataka_shc_npk_district.csv` (`v2`): Corrected district-level SHC dataset (31 rows).
8. `research/shc_karnataka/SHC_MODEL_COMPATIBILITY_AUDIT.md`: Pre-flight compatibility audit.
9. `research/shc_karnataka/shc_vs_production_comparison.csv`: Prior structural comparison table.

### 2. Semantic Mismatch: Ambient Soil Supply vs. Crop Physiological Demand
The most critical finding of this audit is that **the two datasets measure fundamentally different physical and agronomic entities**:

| Parameter | Canonical Training Data (`Crop_recommendation_clean.csv`) | Karnataka SHC Dataset (`karnataka_shc_npk_district.csv`) |
| :--- | :--- | :--- |
| **Agronomic Concept** | **Crop Physiological Demand / Optimum Threshold** | **Ambient Bulk Soil Nutrient Stock** |
| **Measurement Unit** | kg/ha (root-zone nutrient requirement for optimal yield) | kg/ha (extractable elemental macronutrient per hectare) |
| **Laboratory Method** | Agronomic crop response literature / FAO / ICAR tables | Alkaline $KMnO_4$ (N), Olsen/Bray (P), $NH_4OAc$ (K) |
| **Spatial Aggregation**| Per-plant / plot agronomic requirement | District-wide survey averages across thousands of $km^2$ |
| **Target Association** | Explicit 1-to-1 pairing with 23 specific crop species | **Zero crop labels**; survey of general agricultural fields |
| **Nitrogen Range** | Min: $5.53$, Median: $34.61$, Max: **$153.79\text{ kg/ha}$** | Min: $137.60$, Median: $151.10$, Max: **$249.70\text{ kg/ha}$** |
| **Phosphorus Range** | Min: $3.30$, Median: $48.52$, Max: **$177.91\text{ kg/ha}$** | Min: $16.20$, Median: $29.00$, Max: **$46.80\text{ kg/ha}$** |
| **Potassium Range** | Min: $3.54$, Median: $34.08$, Max: **$236.77\text{ kg/ha}$** | Min: $138.50$, Median: $225.80$, Max: **$398.60\text{ kg/ha}$** |

### 3. District Coverage, Nulls, and Duplicates
- **District Coverage**: 30 administrative districts of Karnataka + 1 statewide coverage fallback (`Karnataka coverage`).
- **Missing Values**: Exactly 0 null / NaN values across all 14 columns.
- **Duplicate Rows**: Exactly 0 duplicate districts.

---

## Phase 2 — Baseline Experiment Reproduction

To establish a benchmark, the production Random Forest model was reproduced using the canonical dataset (`datasets/Crop_recommendation_clean.csv`) and the identical training protocol specified in `backend/train_model.py`.

### 1. Protocol Specifications
- **Split**: 80% Train (920 samples) / 20% Test (230 samples), stratified by class label, `random_state=42`.
- **Features**: `['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 'soil_type_encoded']`.
- **Algorithm**: `RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)`.

### 2. Measured Baseline Metrics
- **Overall Accuracy**: **93.04%** (Identical to production model)
- **Macro Precision**: **93.22%**
- **Weighted Precision**: **93.22%**
- **Macro Recall**: **93.04%**
- **Weighted Recall**: **93.04%**
- **Macro F1-Score**: **93.00%**
- **Weighted F1-Score**: **93.00%**
- **Training Time**: **0.4492 seconds**
- **Total Test Inference Time**: **0.1253 seconds** (0.5447 ms per sample)
- **Production Model Match**: **100.00% identical predictions** against `models/crop_model.pkl`.

### 3. Baseline Feature Importances
| Feature | Importance Score | Percentage Contribution |
| :--- | :---: | :---: |
| `rainfall` | 0.1720 | 17.20% |
| `humidity` | 0.1531 | 15.31% |
| `N` (Nitrogen) | 0.1491 | 14.91% |
| `P` (Phosphorus) | 0.1465 | 14.65% |
| `K` (Potassium) | 0.1463 | 14.63% |
| `ph` | 0.0877 | 8.77% |
| `temperature` | 0.0740 | 7.40% |
| `soil_type_encoded` | 0.0713 | 7.13% |

> [!NOTE]
> The three macronutrients ($N, P, K$) jointly account for **44.19% of the total decision weight** in the Random Forest. Therefore, out-of-distribution shifts in $N, P, K$ severely disrupt the model's decision tree branching.

---

## Phase 3 — Label Validity & Data Integrity Constraints

Phase 3 established strict scientific guardrails:
1. **Zero Ground-Truth Crop Labels**: The Soil Health Card portal records soil chemistry tests from farmers' plots. It does **not** record which crops were grown, whether the crops succeeded, or their harvest yields.
2. **Prohibition of Synthetic Labeling**: Assigning crop labels to SHC districts (e.g. assigning "cotton" to Ballari or "ragi" to Tumakuru) creates synthetic circular training data that reflects human bias rather than machine learning ground truth.
3. **Prohibition of Data Inflation**: Duplicating district rows or assigning arbitrary random noise is ungrounded.
4. **Conclusion**: Direct supervised training of a crop recommendation model using SHC data alone is **scientifically impossible** without fabricating training labels.

---

## Phase 4 — Calibration & Domain Adaptation Experiments

We investigated four candidate approaches to determine whether SHC N/P/K values can be legitimately calibrated into the feature space expected by the crop model:

### Approach A: Agronomic / Soil Test Crop Response (STCR) Mapping
- **Theoretical Basis**: In Indian agronomy, fertilizer recommendations are calculated using STCR calibration equations:
  $$\text{Fertilizer Dose } (F) = \frac{\text{Yield Target} \times \text{Nutrient Req}}{\text{Efficiency}} - \frac{\text{Soil Test Value} \times \text{Soil Contribution}}{\text{Efficiency}}$$
- **Evaluation**: STCR equations calculate *how much fertilizer to add* for a **known pre-selected crop**. They cannot be inverted crop-agnostically to calculate *which crop should be grown* from bulk soil tests.
- **Scientific Verdict**: **REJECTED (Category Error)**.

### Approach B: Calibration via Overlapping Reference Anchors ($N = 4$)
In `v1`, four published research station soil profiles served as anchors across Karnataka. We compared these against the corresponding SHC aggregates in `v2`:

| Reference Anchor | v1 N | v2 SHC N | v1 P | v2 SHC P | v1 K | v2 SHC K |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Bengaluru Urban (GKVK)** | 249.70 | 142.10 | 46.80 | 26.90 | 180.40 | 184.10 |
| **Hassan (Hosahalli)** | 369.73 | 222.40 | 9.25 | 38.10 | 265.59 | 218.80 |
| **Dharwad (ARS Annigeri)** | 202.00 | 209.00 | 18.90 | 17.60 | 347.00 | 268.00 |
| **Raichur (UAS Raichur)** | 203.60 | 137.60 | 30.87 | 17.10 | 346.40 | 150.00 |

#### Statistical Correlation Analysis:
- **Available N**: Pearson $r = 0.5476$ ($p = 0.4524$, not statistically significant)
- **Available P**: Pearson $r = -0.3456$ ($p = 0.6544$, **Negative Correlation**)
- **Available K**: Pearson $r = 0.2038$ ($p = 0.7962$, not statistically significant)
- **Scientific Verdict**: **REJECTED**. With only 4 points, degrees of freedom $df = 2$. The correlation is statistically indistinguishable from random noise, and Phosphorus exhibits an inverted (negative) slope, which would bizarrely map higher soil P to lower crop P.

### Approach C: Non-Linear Quantile Domain Adaptation
We tested an empirical `QuantileTransformer` (mapping training N/P/K into uniform quantiles $[0, 1]$):
- **Model Evaluation on Test Split**: Accuracy = **92.61%**, Macro F1 = **92.54%** (slight drop from 93.04%).
- **Districts Exceeding Upper Boundary (Saturation)**:
  - **46.7% of Karnataka districts (14/30)** have $N > 153.8\text{ kg/ha}$, clipping to the 100th percentile ($1.0$).
  - **36.7% of Karnataka districts (11/30)** have $K > 236.8\text{ kg/ha}$, clipping to the 100th percentile ($1.0$).
- **Scientific Verdict**: **REJECTED**. Quantile mapping causes boundary saturation, obliterating differences between districts (e.g. Hassan $N=222$ and Ramanagara $N=250$ both collapse to 1.0).

### Approach D: Explicit Rejection of Calibration
- **Finding**: **A scientifically defensible calibration layer cannot be justified from the available data.**

---

## Phase 5 — Experimental Model vs. Production Baseline

An experimental model benchmark was trained using the quantile domain adaptation pipeline and persisted as `models/crop_model_shc_experimental.pkl` for evaluation purposes:

| Evaluation Metric | Production Baseline Model (`models/crop_model.pkl`) | Experimental Adaptation Model (`models/crop_model_shc_experimental.pkl`) | Performance Delta |
| :--- | :---: | :---: | :---: |
| **Algorithm** | RandomForest (200 trees) | RandomForest (200 trees) + QuantileTransformer | Domain adapted |
| **Test Accuracy** | **93.04%** | **92.61%** | -0.43% |
| **Macro Precision** | **93.22%** | **92.81%** | -0.41% |
| **Macro Recall** | **93.04%** | **92.61%** | -0.43% |
| **Macro F1-Score** | **93.00%** | **92.54%** | -0.46% |
| **Training Time** | **0.4492 s** | **0.4851 s** | +0.0359 s |
| **Inference Time / sample** | **0.5447 ms** | **0.5820 ms** | +0.0373 ms |
| **Out-of-Distribution (OOD) Rate** | **63.3%** (when fed uncalibrated SHC) | **46.7% saturated at 100th percentile** | Boundary clipping |
| **Top-1 Recommendation Churn**| Baseline reference | **23.3% flip** (grapes $\rightarrow$ coffee) | Severe shift |
| **Mean Model Confidence** | 20.6% (heavily fragmented) | 20.2% (heavily fragmented) | -0.4% |

---

## Phase 6 — Full 30-District Controlled Shadow Test

To isolate the exact impact of switching from `v1` proxy N/P/K to `v2` SHC N/P/K, a controlled shadow test was executed across all 30 administrative districts of Karnataka.

### Controlled Environmental Baseline
Standard Karnataka Kharif conditions were held strictly identical across both runs:
- **Temperature**: $26.0^\circ\text{C}$
- **Humidity**: $68.0\%$
- **pH**: $6.50$
- **Rainfall**: $120.0\text{ mm}$
- **Soil Type**: Red Soil (`soil_type_encoded = 3`)

### Shadow Test Results Table (30 Districts)
*Source data saved in: `research/shc_karnataka/shc_model_comparison.csv`*

| District | Old N | Old P | Old K | New N | New P | New K | Old Pred | New Pred | Old Conf | New Conf | Changed? | OOD Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Bengaluru Urban** | 249.7 | 46.8 | 180.4 | 142.1 | 26.9 | 184.1 | grapes | **coffee** | 20.0% | 20.0% | **YES** | In Range |
| **Bengaluru Rural** | 249.7 | 46.8 | 180.4 | 142.8 | 29.1 | 199.9 | grapes | grapes | 20.0% | 21.5% | NO | In Range |
| **Ramanagara** | 249.7 | 46.8 | 180.4 | 249.7 | 46.8 | 180.4 | grapes | grapes | 20.0% | 20.0% | NO | **OOD N** |
| **Chikkaballapur** | 249.7 | 46.8 | 180.4 | 139.3 | 34.8 | 229.7 | grapes | grapes | 20.0% | 21.0% | NO | In Range |
| **Kolar** | 249.7 | 46.8 | 180.4 | 142.8 | 32.9 | 175.1 | grapes | grapes | 20.0% | 19.5% | NO | In Range |
| **Tumakuru** | 249.7 | 46.8 | 180.4 | 150.1 | 31.3 | 221.8 | grapes | grapes | 20.0% | 21.5% | NO | In Range |
| **Hassan** | 369.7 | 9.2 | 265.6 | 222.4 | 38.1 | 218.8 | grapes | grapes | 20.5% | 21.5% | NO | **OOD N** |
| **Mysuru** | 369.7 | 9.2 | 265.6 | 137.9 | 34.6 | 252.5 | grapes | grapes | 20.5% | 21.0% | NO | **OOD K** |
| **Mandya** | 369.7 | 9.2 | 265.6 | 150.2 | 33.6 | 234.4 | grapes | grapes | 20.5% | 21.0% | NO | In Range |
| **Chamarajanagar** | 369.7 | 9.2 | 265.6 | 220.8 | 31.1 | 180.1 | grapes | grapes | 20.5% | 19.5% | NO | **OOD N** |
| **Kodagu** | 369.7 | 9.2 | 265.6 | 211.8 | 28.8 | 250.6 | grapes | **coffee** | 20.5% | 20.5% | **YES** | **OOD N & K** |
| **Chikkamagaluru** | 369.7 | 9.2 | 265.6 | 149.4 | 35.5 | 253.7 | grapes | grapes | 20.5% | 21.0% | NO | **OOD K** |
| **Dakshina Kannada**| 369.7 | 9.2 | 265.6 | 140.1 | 22.5 | 138.5 | grapes | **coffee** | 20.5% | 19.0% | **YES** | In Range |
| **Udupi** | 369.7 | 9.2 | 265.6 | 169.3 | 27.5 | 172.9 | grapes | **coffee** | 20.5% | 20.0% | **YES** | **OOD N** |
| **Shivamogga** | 369.7 | 9.2 | 265.6 | 155.8 | 25.5 | 265.6 | grapes | grapes | 20.5% | 20.5% | NO | **OOD N & K** |
| **Uttara Kannada** | 369.7 | 9.2 | 265.6 | 152.1 | 24.7 | 194.0 | grapes | **coffee** | 20.5% | 20.0% | **YES** | In Range |
| **Belagavi** | 202.0 | 18.9 | 347.0 | 143.5 | 22.3 | 212.7 | grapes | grapes | 20.5% | 21.0% | NO | In Range |
| **Dharwad** | 202.0 | 18.9 | 347.0 | 209.0 | 17.6 | 268.0 | grapes | grapes | 20.5% | 20.5% | NO | **OOD N & K** |
| **Gadag** | 202.0 | 18.9 | 347.0 | 208.4 | 19.0 | 254.1 | grapes | grapes | 20.5% | 20.5% | NO | **OOD N & K** |
| **Haveri** | 202.0 | 18.9 | 347.0 | 191.6 | 18.5 | 191.3 | grapes | grapes | 20.5% | 20.0% | NO | **OOD N** |
| **Bagalkot** | 203.6 | 30.9 | 346.4 | 171.5 | 24.7 | 235.4 | grapes | grapes | 21.0% | 20.5% | NO | **OOD N** |
| **Vijayapura** | 203.6 | 30.9 | 346.4 | 138.9 | 37.2 | 251.2 | grapes | grapes | 21.0% | 21.0% | NO | **OOD K** |
| **Koppal** | 203.6 | 30.9 | 346.4 | 227.4 | 37.5 | 287.8 | grapes | grapes | 21.0% | 21.0% | NO | **OOD N & K** |
| **Raichur** | 203.6 | 30.9 | 346.4 | 137.6 | 17.1 | 150.0 | grapes | grapes | 21.0% | 18.0% | NO | In Range |
| **Yadgir** | 203.6 | 30.9 | 346.4 | 149.2 | 32.9 | 373.5 | grapes | grapes | 21.0% | 21.0% | NO | **OOD K** |
| **Kalaburagi** | 250.0 | 75.0 | 390.0 | 150.0 | 38.9 | 398.6 | grapes | grapes | 22.0% | 21.0% | NO | **OOD K** |
| **Bidar** | 203.6 | 30.9 | 346.4 | 177.8 | 16.2 | 396.5 | grapes | grapes | 21.0% | 20.5% | NO | **OOD N & K** |
| **Ballari** | 203.6 | 30.9 | 346.4 | 200.3 | 23.4 | 184.8 | grapes | **coffee** | 21.0% | 19.0% | **YES** | **OOD N** |
| **Vijayanagara** | 203.6 | 30.9 | 346.4 | 178.0 | 25.2 | 160.4 | grapes | **coffee** | 21.0% | 20.0% | **YES** | **OOD N** |
| **Chitradurga** | 202.0 | 18.9 | 347.0 | 141.4 | 34.6 | 236.3 | grapes | grapes | 20.5% | 21.0% | NO | In Range |

---

## Phase 7 — Safety Check & Agronomic Diagnostics

### 1. Severe Out-of-Distribution (OOD) Shift
- **Overall OOD Rate**: **19 out of 30 districts (63.3%)** have values exceeding the training boundaries of the model.
- **Nitrogen Exceedances**: 14 districts (46.7%) exceed $153.79\text{ kg/ha}$ (reaching up to $249.70\text{ kg/ha}$ in Ramanagara, $+62.4\%$ above maximum).
- **Potassium Exceedances**: 11 districts (36.7%) exceed $236.77\text{ kg/ha}$ (reaching up to $398.60\text{ kg/ha}$ in Kalaburagi, $+68.3\%$ above maximum).

### 2. Monoculture Crop Recommendations & Confidence Dilution
- In both runs, the model predicts **only two crops** out of 23 possible classes across all 30 districts: `grapes` (23 districts) and `coffee` (7 districts).
- Neither recommendation reflects realistic Karnataka agriculture (which is dominated by ragi, jowar, maize, paddy, cotton, groundnut, and pulses).
- **Confidence Dilution**: Model confidence across all 30 districts is between **18.0% and 21.5%** (barely above a random uniform prior of $1/23 = 4.3\%$). Over 78% of the probability is scattered across irrelevant classes because the decision trees have never encountered high K ($> 150$) combined with low P ($< 40$) and high N ($> 140$).

### 3. Behavioral Instability vs. Real Improvement
The 7 districts that changed recommendation (Bengaluru Urban, Kodagu, Dakshina Kannada, Udupi, Uttara Kannada, Ballari, Vijayanagara) did not change because the model "discovered" a better crop. They changed purely because Potassium fell just below the split threshold that forces `grapes`, shifting the prediction to `coffee` with a weak 19% confidence. Recommending coffee for Ballari (a dry, semi-arid northern Deccan plain) is agronomically absurd.

---

## Phase 8 — Decision & Strategic Roadmap

### Definitive Recommendation:
### **D. SHC DATA IS NOT CURRENTLY SUITABLE FOR PRODUCTION**

```
                  ┌────────────────────────────────────────────────────────┐
                  │ DECISION: D. SHC DATA NOT SUITABLE FOR PRODUCTION      │
                  └────────────────────────┬───────────────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         ▼                                                                   ▼
┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
│ Immediate Action (Production):  │                         │ Long-Term Roadmap (Research):   │
│ - KEEP current v1 lookup        │                         │ - RETRAIN using ICAR / STCR     │
│ - MAINTAIN crop_model.pkl       │                         │   paired field trials (Opt. C)  │
│ - ZERO production code changes  │                         │ - Ingest real crop-yield data   │
└─────────────────────────────────┘                         └─────────────────────────────────┘
```

### Justification Based on Empirical Findings:
1. **Direct deployment violates model safety**: 63.3% of Karnataka districts are out-of-distribution, forcing the Random Forest to extrapolate in unknown feature space.
2. **Calibration cannot be scientifically defended**: With $N=4$ anchor points and negative P correlation, fitting a mathematical conversion is statistically ungrounded. Quantile adaptation collapses 46.7% of districts to the same boundary.
3. **SHC lacks crop labels**: The SHC dataset measures bulk soil nutrient supply, whereas the crop model was trained on crop physiological nutrient demand.
4. **Agronomic absurdity**: Uncalibrated SHC inputs cause the model to recommend `coffee` in semi-arid Ballari with 19% confidence.

### Long-Term Engineering Recommendation (Strategic Option C):
To achieve true, defensible Soil Health Card integration, CropSense AI must eventually execute **Option C (Retrain/rebuild the model using a better validated dataset)** by:
1. Sourcing multi-crop Soil Test Crop Response (STCR) field trial data from ICAR and State Agricultural Universities (UAS Bangalore, UAS Dharwad).
2. Explicitly parameterizing the model to take **soil supply** ($N_{soil}, P_{soil}, K_{soil}$) and **crop demand** as distinct features.
3. Incorporating localized agro-ecological zones, irrigation status, and soil texture rather than relying on ungrounded mathematical proxies.

---

## Phase 9 — Production File Integrity Guarantee

In strict accordance with project safety constraints, all production assets remain **100% untouched and unaltered**:

- `models/crop_model.pkl` : **UNTOUCHED** (MD5 intact, production 8-feature RF active)
- `datasets/Crop_recommendation_clean.csv` : **UNTOUCHED** (Canonical 1,150-row dataset intact)
- `backend/predict_api.py` : **UNTOUCHED**
- `backend/main.py` : **UNTOUCHED**
- `backend/npk_lookup.py` : **UNTOUCHED**
- `data/karnataka_main_places_npk_project_ready_v1.csv` : **UNTOUCHED**
- `frontend/` : **UNTOUCHED**

All experimental artifacts and scripts remain strictly isolated under:
- `research/shc_karnataka/`
- `models/crop_model_shc_experimental.pkl` (experimental benchmark only)
