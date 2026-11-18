# Known Limitations & Agronomic Distribution Shift

## 1. NPK Input Distribution Shift

The production crop recommendation model (`models/crop_model.pkl`) is a 200-estimator Random Forest trained on an empirical multi-class dataset (`datasets/Crop_recommendation_clean.csv`, 1,150 samples across 23 classes).

The empirical feature ranges observed during model training are:
- **Nitrogen ($N$)**: $[5.5, 153.8]\text{ kg/ha}$
- **Phosphorus ($P$)**: $[3.3, 177.9]\text{ kg/ha}$
- **Potassium ($K$)**: $[3.5, 236.8]\text{ kg/ha}$

In contrast, the geospatial reference dataset (`data/karnataka_main_places_npk_project_ready_v1.csv`) supplies measured and regional proxy available nutrient profiles for Karnataka districts where:
- Available $N$ values range from **$202.0\text{ to }369.7\text{ kg/ha}$** (e.g., Bengaluru Urban GKVK: $249.7\text{ kg/ha}$, Dharwad ARS Annigeri: $202.0\text{ kg/ha}$).
- Available $K$ values range up to **$390.0\text{ kg/ha}$** (e.g., Kalaburagi profile: $390.0\text{ kg/ha}$, Belagavi anchor: $347.0\text{ kg/ha}$).

Because the runtime NPK inputs frequently exceed the upper bounds of the training distribution, the Random Forest model operates in an extrapolative regime.

---

## 2. Quantitative Root-Cause Audit Findings

A comprehensive grid audit was executed across **73 Karnataka locations** under **5 representative weather scenarios** ($73 \times 5 = 365$ runs) using the production Random Forest before crop filtering:

| Metric | Measured Value | Agronomic Rationale |
| :--- | :--- | :--- |
| **Total Test Runs** | 365 | Comprehensive geographic and climatic grid |
| **$N$ Out-of-Distribution** | **100.0%** (365 / 365) | All regional profiles report $N \ge 202.0\text{ kg/ha}$ |
| **$K$ Out-of-Distribution** | **75.3%** (275 / 365) | Northern and Interior districts exceed $236.8\text{ kg/ha}$ |
| **$P$ Out-of-Distribution** | **0.0%** (0 / 365) | Available $P$ values fall within training range |
| **Statewide Fallback Hits** | **0.0%** (0 / 365) | KD-Tree nearest-neighbor lookup succeeded for 100% of locations |

### Top-1 Prediction Frequencies (Unfiltered Model Output)
Before applying the field crop filter, predictions were heavily dominated by fruit classes:
- **Apple**: 47.40% (173 runs)
- **Grapes**: 33.42% (122 runs)
- **Muskmelon**: 6.58% (24 runs)
- **Banana**: 0.55% (2 runs)
- **Total Fruit / Tree Dominance**: **87.95%** (321 / 365 runs)
- **Field Crops (Maize, Rice, Chickpea, Cotton, etc.)**: **12.05%** (44 / 365 runs)

In the training corpus, the extreme upper quantiles of $N$ and $K$ are predominantly associated with high-feeder horticultural fruits (Grapes, Apple, Muskmelon). Consequently, tree split thresholds route out-of-distribution field inputs into leaf nodes dedicated to these fruits, yielding low-confidence ($\sim 20\text{--}30\%$) fruit recommendations.

---

## 3. Rationale for the Field Crop Filter

To ensure actionable utility for field farmers while preserving scientific honesty:
1. **Full Distribution Sorting**: The model calculates raw `predict_proba` across all 23 classes first.
2. **Horticultural Filtering**: Ten fruit/tree crops (`apple`, `banana`, `grapes`, `mango`, `muskmelon`, `orange`, `papaya`, `pomegranate`, `watermelon`, `coconut`) are excluded from presentation.
3. **Top-3 Field Crops**: The top 3 ranked field crops (e.g., Maize, Cotton, Wheat, Chickpea, Jute, Rice) are presented.
4. **Probability Transparency**: Raw model probabilities are displayed directly without artificial scaling, normalization, or clipping.
5. **Reversibility**: The `include_fruits` parameter (default `False`) allows accessing unfiltered predictions for research and demonstration.

---

## 4. Why Input Calibration Was Tested and Rejected

Calibration methods (such as min-max clipping, percentile matching, or heuristic scale multipliers) were investigated and explicitly rejected:
- **Agronomic Distortion**: Artificial scaling compresses genuine soil nutrient differences and distorts relative distances between regions.
- **False Precision**: Artificially rescaling inputs to force higher confidence masks the underlying model limitations.
- **Explicit OOD Notice**: The system instead exposes transparent out-of-distribution indicators (`npk_out_of_training_range: true`, `ood_warning: "..."`), informing users and agronomists that the model is extrapolating.

---

## 5. Future Work

Long-term resolution of this distribution gap requires:
1. **Curating Karnataka Soil-Crop Datasets**: Assembling field-trial and Soil Health Card (SHC) datasets where crop yield and soil test measurements follow standard Indian laboratory conventions (alkaline permanganate for $N$, Olsen/Bray for $P$, ammonium acetate for $K$).
2. **Retraining Production Model**: Re-estimating tree split thresholds directly on regional agricultural field data rather than relying on legacy synthetic distributions.
