# Soil Health Card (SHC) & SoilGrids Calibration: Final Research & Decision Report

**Project**: CropSense AI — Soil Nutrient Modeling Research  
**Document**: Final Calibration & Feasibility Report (Phase 15)  
**Date**: October 2026  
**Status**: Research Concluded — **RECOMMENDATION: DO NOT DEPLOY TO PRODUCTION YET**  
**Isolation**: All experimental artifacts strictly isolated under `research/shc_calibration/`  

---

## Executive Summary & Core Verdict

We have completed a comprehensive scientific audit, covariate ingestion, regression modeling, spatial cross-validation, and end-to-end shadow evaluation of the supplied Soil Health Card (SHC) and ISRIC SoilGrids datasets.

### Definitive Verdict:
**The supplied SHC + SoilGrids regression pipeline is NOT ready for production integration.**  
While the regression pipeline is mathematically functional and successfully trained, it exhibits severe structural, regional, and distribution mismatches:
1. **Severe Regional Degradation in Karnataka**: On Karnataka districts specifically, out-of-fold $R^2$ for Available Nitrogen is **negative** ($R^2 = -0.2566$, $\text{MAE} = 30.17\text{ kg/ha}$ vs baseline $\text{MAE} = 28.61\text{ kg/ha}$). The national model performs **worse than a naive mean baseline** when evaluated on Karnataka soils.
2. **Artificial Target Compression**: The supplied SHC processing methodology converts categorical survey counts into continuous estimates using conservative midpoint constants ($137.5, 210.0, 297.5\text{ kg/ha}$ for N). This artificially compresses nationwide Available Nitrogen into $[137.5, 296.2]\text{ kg/ha}$, distorting physical reality.
3. **Severe Out-of-Distribution (OOD) Shift**: **52.0% of regression Nitrogen predictions** exceed the maximum Nitrogen value ($153.8\text{ kg/ha}$) ever seen by the production crop recommendation model during training. Furthermore, **35.5% of Potassium predictions** exceed the crop model's maximum Potassium bound ($236.8\text{ kg/ha}$).
4. **Recommendation Instability**: In end-to-end shadow testing across representative Karnataka locations, switching from lookup NPK to regression NPK caused **40.0% of recommended crops to change**, often causing the model to substitute high-confidence primary crops (e.g. Maize, Watermelon) with lower-confidence alternatives (e.g. Grapes).
5. **Production Safety**: All production assets (`models/crop_model.pkl`, `backend/predict_api.py`, `backend/npk_lookup.py`, `backend/train_model.py`, `datasets/Crop_recommendation_clean.csv`, `frontend/`) remain **100% untouched and unchanged**. The production system safely continues utilizing the established Karnataka spatial lookup.

---

## Comprehensive Answers to the 14 Required Evaluation Questions

### 1. Is the supplied SHC dataset suitable for calibration?
**Partially suitable as a macro-regional research exploration, but NOT suitable as a direct drop-in replacement for production.**  
The raw SHC data consists of aggregated sample counts binned into 3 coarse fertility categories (Low, Medium, High). The continuous targets were artificially synthesized by taking frequency-weighted averages of fixed category midpoints. This collapses intra-district variance, ignores sub-district soil heterogeneity, and imposes artificial mathematical floors and ceilings on all nutrient values.

### 2. How many usable observations are available?
- **Raw table rows**: 6,600 rows (reflecting a 5-fold duplication from a multi-index groupby join in `build_dataset.py`).
- **Unique district-year observations in SHC targets**: **1,320**.
- **Observations with successful SoilGrids covariate joins**: **1,100 clean observations** (220 lost due to missing coordinates or SoilGrids unmapped/coastal pixels).
- **Usable observations for N, P, K**: Exactly **1,100** complete pairs across targets and all 12 SoilGrids covariates.

### 3. How many districts?
- **Total districts in supplied SHC**: 717 unique districts across 32 States & UTs.
- **Districts with valid coordinates**: 635 districts.
- **Districts in final clean calibration dataset**: **600 unique districts** nationwide.

### 4. How much Karnataka data is available?
- **Total Karnataka observations in SHC**: 62 district-years (31 in 2023-24, 31 in 2024-25).
- **Unique Karnataka districts represented**: **31 districts** (100% of Karnataka administrative districts).
- **Karnataka districts with georeferenced coordinates**: 29 districts (58 district-year observations).
- **Karnataka districts with 100% complete SoilGrids covariates**: **29 districts (58 complete observations)**. 2 districts (`Chamarajanagar` and `Vijayanagara`) lacked coordinates in the pre-joined file.

### 5. How well can available N be predicted?
- **National 5-Fold GroupKFold CV**:
  - $R^2 = 0.3752$
  - $\text{MAE} = 19.51\text{ kg/ha}$ (vs baseline $\text{MAE} = 27.15\text{ kg/ha}$, a 28.2% improvement)
  - $\text{RMSE} = 26.50\text{ kg/ha}$
  - $\text{MedAE} = 14.32\text{ kg/ha}$
- **Karnataka Slice Performance**:
  - $R^2 = -0.2566$ (**Negative $R^2$**)
  - $\text{MAE} = 30.17\text{ kg/ha}$ (vs baseline $\text{MAE} = 28.61\text{ kg/ha}$, **worse than naive mean**)
  - $\text{RMSE} = 37.23\text{ kg/ha}$
  - $\text{MedAE} = 24.81\text{ kg/ha}$

### 6. How well can available P be predicted?
- **National 5-Fold GroupKFold CV**:
  - $R^2 = 0.1548$ (very weak predictive power)
  - $\text{MAE} = 6.76\text{ kg/ha}$ (vs baseline $\text{MAE} = 7.66\text{ kg/ha}$, 11.6% improvement)
  - $\text{RMSE} = 8.05\text{ kg/ha}$
  - $\text{MedAE} = 6.29\text{ kg/ha}$
- **Karnataka Slice Performance**:
  - $R^2 = 0.0709$
  - $\text{MAE} = 5.85\text{ kg/ha}$ (vs baseline $\text{MAE} = 7.30\text{ kg/ha}$)
  - $\text{RMSE} = 6.91\text{ kg/ha}$

### 7. How well can available K be predicted?
- **National 5-Fold GroupKFold CV**:
  - $R^2 = 0.2832$
  - $\text{MAE} = 53.82\text{ kg/ha}$ (vs baseline $\text{MAE} = 67.57\text{ kg/ha}$, 20.3% improvement)
  - $\text{RMSE} = 67.47\text{ kg/ha}$
  - $\text{MedAE} = 45.65\text{ kg/ha}$
- **Karnataka Slice Performance**:
  - $R^2 = 0.1297$
  - $\text{MAE} = 57.64\text{ kg/ha}$ (vs baseline $\text{MAE} = 58.20\text{ kg/ha}$, marginal 1% improvement)
  - $\text{RMSE} = 69.64\text{ kg/ha}$

### 8. Which SoilGrids variables are most useful?
- **For Nitrogen ($N$)**:
  1. `phh2o_0-30cm` (15.71%)
  2. `phh2o_0-5cm` (13.70%)
  3. `nitrogen_0-30cm` (11.85%)
  4. `nitrogen_0-5cm` (8.25%)
  *Insight*: Soil pH strongly governs microbial mineralization rates, while SoilGrids total nitrogen provides a weak background organic pool constraint.
- **For Phosphorus ($P$)**:
  1. `nitrogen_0-5cm` (9.91%)
  2. `nitrogen_0-30cm` (9.55%)
  3. `soc_0-30cm` (9.00%)
  4. `cec_0-30cm` (8.99%)
  *Insight*: Features exhibit uniform, flat importances (~8–10% each). SoilGrids contains no direct spectroscopic or chemical proxy for labile/extractable orthophosphate.
- **For Potassium ($K$)**:
  1. `cec_0-30cm` (14.03%)
  2. `cec_0-5cm` (13.10%)
  3. `soc_0-5cm` (9.51%)
  4. `clay_0-5cm` (8.57%)
  *Insight*: Cation Exchange Capacity (CEC) and clay content are sound pedological drivers of exchangeable $K^+$ retention.

### 9. Are the regression errors acceptable?
**NO.**  
For Available Nitrogen, a national MAE of $19.5\text{ kg/ha}$ might appear tolerable on paper, but an MAE of $30.2\text{ kg/ha}$ with a negative $R^2$ in Karnataka means the model introduces random error rather than genuine predictive signal in the primary deployment geography. For Phosphorus, $R^2 = 0.15$ indicates the model explains almost none of the observed variance. For Potassium, an MAE of $53.8\text{ kg/ha}$ (and $57.6\text{ kg/ha}$ in Karnataka) represents substantial error on soils where crop response curves are sensitive.

### 10. How different are regression N/P/K values from the current lookup values?
They diverge substantially:
- Across Karnataka test locations:
  - $N$ differed by **-29.8% to -61.3%** (regression predictions were systematically lower than the lookup table, e.g. Mysuru dropped from $369.7$ to $143.0\text{ kg/ha}$).
  - $P$ differed by **+16.2% to +279.1%** (regression predictions were higher in low-P districts, e.g. Mysuru rose from $9.2$ to $31.4\text{ kg/ha}$).
  - $K$ differed by **-3.7% to -39.8%** (regression predictions were lower in high-K districts, e.g. Raichur dropped from $346.4$ to $208.7\text{ kg/ha}$).

### 11. How often does the resulting crop recommendation change?
**In 4 out of 10 representative Karnataka locations (40.0% change rate).**  
Specific crop transitions observed:
- Bengaluru Urban: Maize (22.0% conf) $\rightarrow$ Grapes (19.5% conf)
- Mysuru: Watermelon (25.5% conf) $\rightarrow$ Grapes (20.0% conf)
- Hassan: Watermelon (25.5% conf) $\rightarrow$ Grapes (20.0% conf)
- Udupi: Apple (19.5% conf) $\rightarrow$ Coffee (23.5% conf)
*(Note: While Udupi recommending Coffee is agronomically superior to Apple, Mysuru and Hassan shifting to Grapes occurs because regression NPK suppresses N and inflates P into a profile favored by temperate/horticultural crops in the training dataset).*

### 12. Does the experimental approach appear promising?
**Conceptually yes, but the current data foundation is inadequate.**  
Using remote sensing/gridded covariates (pH, CEC, texture, SOC) to predict available nutrients (pedotransfer functions) is scientifically viable. However, calibrating these models against **coarse, 3-bin categorical SHC summaries** severely truncates variance and introduces mathematical distortions. Calibration requires **raw, continuous laboratory soil test measurements** from agricultural universities or ICAR regional research centers.

### 13. What limitations remain?
1. **Aggregated Survey vs Lab Measurements**: The target data is derived from category midpoints, not physical lab extractions.
2. **Artificial Bounding**: Nitrogen is artificially constrained to $[137.5, 297.5]\text{ kg/ha}$ due to conservative midpoint selection in `build_dataset.py`.
3. **Out-of-Distribution Coupling**: The downstream crop recommendation model was trained on an entirely different distribution ($N \in [5.5, 153.8]$), creating severe distributional incompatibility.
4. **SoilGrids REST API Volatility**: ISRIC's public REST API is officially paused/intermittent, frequently timing out or returning 503 errors during real-time queries.
5. **Urban & Sealed Pixels**: SoilGrids returns nulls for urban centers (e.g. Bengaluru Urban, parts of Mysuru), necessitating an automatic fallback regardless.

### 14. Is it safe to integrate into production yet?
**ABSOLUTELY NOT.**  
Integrating this regression pipeline would immediately:
- Degrade Nitrogen prediction accuracy across Karnataka compared to the existing lookup table.
- Induce out-of-distribution extrapolation in 52% of all downstream crop predictions.
- Introduce reliance on an unstable third-party REST API that is currently paused by ISRIC.

---

## Critical Scientific Distinction: Model Accuracy Handoff

> [!CAUTION]
> **Scientific Rule Violation Alert**: Do NOT claim that the new regression pipeline maintains CropSense AI's 93.04% crop recommendation accuracy.
> 
> - **The 93.04% Accuracy Benchmark**: This figure was measured strictly using the **existing Karnataka spatial lookup table** as the input source for $N, P, K$.
> - **Error Propagation**: The regression models introduce an average error of $\pm 19.5\text{ kg/ha}$ for N, $\pm 6.8\text{ kg/ha}$ for P, and $\pm 53.8\text{ kg/ha}$ for K. When these noisy inputs are fed into the non-linear decision boundaries of the Random Forest classifier, crop recommendations shifted in 40% of test cases.
> - **True Pipeline Performance**: The end-to-end accuracy of the regression-coupled pipeline is unverified and demonstrably subject to out-of-distribution drift.

---

## Detailed Data & Metric Reference Tables

### Table 1: National Regression Cross-Validation Metrics (5-Fold GroupKFold)
| Target Variable | Algorithm | Covariates ($p$) | Samples ($n$) | Model $R^2$ | Model MAE (kg/ha) | Model RMSE (kg/ha) | Baseline MAE (kg/ha) | Improvement |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Available N** | RandomForest | 12 | 1,100 | **0.3752** | **19.51** | 26.50 | 27.15 | +28.2% |
| **Available P** | RandomForest | 12 | 1,100 | **0.1548** | **6.76** | 8.05 | 7.66 | +11.6% |
| **Available K** | RandomForest | 12 | 1,100 | **0.2832** | **53.82** | 67.47 | 67.57 | +20.3% |

### Table 2: Regional Performance Sliced on Karnataka ($n=58$)
| Target Variable | Karnataka Model $R^2$ | Karnataka Model MAE | Karnataka Baseline MAE | Evaluation Verdict |
| :--- | :---: | :---: | :---: | :--- |
| **Available N** | **-0.2566** | **30.17 kg/ha** | 28.61 kg/ha | **FAILED (Worse than naive mean)** |
| **Available P** | **0.0709** | **5.85 kg/ha** | 7.30 kg/ha | Marginal explanatory signal |
| **Available K** | **0.1297** | **57.64 kg/ha** | 58.20 kg/ha | Marginal explanatory signal |

### Table 3: Out-of-Distribution (OOD) Analysis vs Crop Recommendation Training Set
| Nutrient | Crop Model Training Min | Crop Model Training Max | Regression Output Min | Regression Output Max | Observations Above Max ($> \text{Max}$) | % Out of Distribution |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Nitrogen ($N$)** | 5.53 kg/ha | **153.79 kg/ha** | 137.75 kg/ha | **246.31 kg/ha** | **572 / 1,100** | **52.00% ⚠️** |
| **Phosphorus ($P$)**| 3.30 kg/ha | **177.91 kg/ha** | 13.58 kg/ha | **36.98 kg/ha** | 0 / 1,100 | 0.00% (Severely compressed) |
| **Potassium ($K$)** | 3.54 kg/ha | **236.77 kg/ha** | 113.47 kg/ha | **365.91 kg/ha** | **390 / 1,100** | **35.45% ⚠️** |

---

## Exact Inventory of Artifacts Created in Research Directory

All artifacts are strictly contained under `research/shc_calibration/`:

1. [`DATA_AUDIT.md`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/DATA_AUDIT.md) — Comprehensive 14-point audit of all supplied files, data types, and limitations.
2. [`FALLBACK_ARCHITECTURE.md`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/FALLBACK_ARCHITECTURE.md) — Specification for the future primary/fallback architecture.
3. [`SHC_CALIBRATION_FINAL_REPORT.md`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/SHC_CALIBRATION_FINAL_REPORT.md) — This complete decision document.
4. [`shc_with_covariates.csv`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/shc_with_covariates.csv) — Intermediate dataset joining SHC targets with SoilGrids covariates.
5. [`shc_soilgrids_training.csv`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/shc_soilgrids_training.csv) — Clean, validated training dataset (1,100 observations across 600 districts).
6. [`soilgrids_cache.json`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/soilgrids_cache.json) — Local persistent cache containing 616 queried coordinates.
7. [`soilgrids_failed.json`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/soilgrids_failed.json) — Audit log of 16 failed/unmapped coordinates.
8. [`oof_predictions.csv`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/oof_predictions.csv) — Leakage-safe 5-fold GroupKFold predictions for all national observations.
9. [`shadow_test_results.csv`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/shadow_test_results.csv) — Detailed location-by-location shadow comparison for 10 representative Karnataka locations.
10. [`ood_analysis.json`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/ood_analysis.json) — Statistical quantiles and OOD counts for N, P, and K.
11. [`model_metadata.json`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/model_metadata.json) — Model hyperparameters, training date, feature lists, and validation metrics.
12. [`models/available_n_model.joblib`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/models/available_n_model.joblib) — Trained experimental Random Forest regressor for Available N.
13. [`models/available_p_model.joblib`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/models/available_p_model.joblib) — Trained experimental Random Forest regressor for Available P.
14. [`models/available_k_model.joblib`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/models/available_k_model.joblib) — Trained experimental Random Forest regressor for Available K.
15. [`experimental_npk_provider.py`](file:///c:/Users/shree/Downloads/major-project-demo1/research/shc_calibration/experimental_npk_provider.py) — Isolated experimental inference interface.

---

## Production Verification Statement

We verify that **NO PRODUCTION FILES WERE ALTERED**:
- `models/crop_model.pkl`: UNCHANGED (verified checksum and modification status)
- `backend/predict_api.py`: UNCHANGED
- `backend/npk_lookup.py`: UNCHANGED
- `backend/train_model.py`: UNCHANGED
- `datasets/Crop_recommendation_clean.csv`: UNCHANGED
- `frontend/`: UNCHANGED

The CropSense AI production system remains intact, secure, and running on the verified Karnataka lookup profile.
