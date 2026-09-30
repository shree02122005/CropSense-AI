# CropSense AI — N/P/K Inference Compatibility & Out-of-Distribution (OOD) Analysis

**Document Version:** 1.0  
**Scope:** Engineering Audit, Out-of-Distribution Handling, and Inference Pipeline Architecture  
**Date:** September 2026  
**System:** CropSense AI (Precision Agricultural Advisory Platform)

---

## 1. Executive Summary & Core Objective

The objective of this engineering intervention is to allow legitimate, published Karnataka soil macronutrient profiles ($N, P, K$) to flow into the crop recommendation model without artificial rejection, while maintaining complete scientific integrity:

1. **No Artificial Range Restrictions or Clipping:** Raw measured soil test values from peer-reviewed university research and ICAR surveys across Karnataka are passed directly into the model's feature vector without artificial clipping, min-max scaling, or normalization.
2. **Transparent Out-of-Distribution (OOD) Flagging:** When an input feature falls outside the empirical training boundary, it is tagged with structured OOD diagnostic metadata (`npk_out_of_training_range: True`, `npk_ood_features: ["N", "K"]`, and `ood_warning`).
3. **No False Validation Claims:** Removing range restrictions allows the system to run on real data, but it does **not** solve the underlying semantic mismatch between native soil reserves and crop fertilizer requirements. Predictions on OOD inputs represent algorithmic tree extrapolation and are explicitly documented as an identified research boundary.

---

## 2. Why Legitimate Inference Values Exceed the Training Range

A fundamental finding of our data audit is that the training dataset and the inference dataset represent two distinct agronomic concepts that share the same unit label ($\text{kg/ha}$):

### A. The Training Dataset (`Crop_recommendation_clean.csv`)
- **Underlying Concept:** Represents **Crop Nutrient Demand / Recommended Dose of Fertilizers (RDF)**.
- **Evidence:**
  - Legumes (kidneybeans, lentil, mothbeans, mungbean, pigeonpeas) have $N \in [5.5, 35]\text{ kg/ha}$. In agricultural practice, legumes fix atmospheric nitrogen via symbiotic root nodules (*Rhizobium*); they require only a modest starter dose of nitrogen fertilizer. A natural soil with only $10\text{ kg/ha}$ available N would be sterile subsoil.
  - Grapes ($K = 156–228\text{ kg/ha}$) and Apple ($K = 149–237\text{ kg/ha}$) have very high potassium values in the dataset, reflecting the intensive potassium fertilizer applications required for commercial fruit orchards. All other 21 crops in the training dataset have $K < 75\text{ kg/ha}$.
- **Empirical Boundaries:**
  - $N$: **5.53 to 153.79 kg/ha**
  - $P$: **3.30 to 177.91 kg/ha**
  - $K$: **3.54 to 236.77 kg/ha**

### B. The Inference Dataset (`karnataka_main_places_npk_project_ready_v1.csv`)
- **Underlying Concept:** Represents **Native Soil Available Nutrient Reserves (Soil Test Extractable Pools)** in the surface plow layer ($0 - 15\text{ cm}$).
- **Chemical Methodologies:**
  - **Available N:** Alkaline permanganate distillation ($\text{KMnO}_4 + \text{NaOH}$) (Subbiah & Asija, 1956). Measures mineralizable organic nitrogen.
  - **Available P:** Olsen's $0.5\text{ M NaHCO}_3$ extractant spectrophotometry (Olsen et al., 1954).
  - **Available K:** Neutral normal $1.0\text{ N NH}_4\text{OAc}$ extraction with flame photometry (Hanway & Heidel, 1952).
- **Empirical Ranges Across Karnataka:**
  - $N$: **202.00 to 369.73 kg/ha** (Indian soil science classifies $< 280\text{ kg/ha}$ as "Low" and $280–560\text{ kg/ha}$ as "Medium" available N).
  - $P$: **9.25 to 75.00 kg/ha** (Low in Hassan/Kodagu, High in Kalaburagi calcareous vertisols).
  - $K$: **180.40 to 390.00 kg/ha** (Karnataka vertisols contain expanding 2:1 smectite clays naturally rich in exchangeable potassium).

---

## 3. Training vs. Inference Numerical Range Comparison

| Feature | Physical Unit | Training Range (Min – Max) | Training Mean | Observed Inference Range (Karnataka) | Out-of-Distribution Status |
|---|---|---|---|---|---|
| **Available Nitrogen (N)** | kg/ha | **5.53 – 153.79** | 50.90 | **202.00 – 369.73** | **OOD High** (1.31× to 2.40× training max) |
| **Available Phosphorus (P)** | kg/ha | **3.30 – 177.91** | 51.65 | **9.25 – 75.00** | **In-Distribution** (within training envelope) |
| **Available Potassium (K)** | kg/ha | **3.54 – 236.77** | 48.85 | **180.40 – 390.00** | **OOD High** (up to 1.65× training max) |
| **Temperature** | °C | **11.54 – 40.50** | 25.21 | **26.9 – 32.9** | **In-Distribution** |
| **Humidity** | % | **1.76 – 100.00** | 68.59 | **37.0 – 72.0** | **In-Distribution** |
| **Soil pH** | Scale (0–14) | **4.90 – 7.76** | 6.46 | **5.80 – 6.20** | **In-Distribution** |
| **Rainfall** | mm | **7.39 – 315.58** | 101.39 | **0.0 – 1.5** (hourly live) | **In-Distribution** |

---

## 4. Why Values Are NOT Clipped or Artificially Scaled

In machine learning pipelines, a common naive fix for out-of-distribution inputs is numerical clipping:
$$\tilde{x} = \min(\max(x, x_{\min}), x_{\max})$$
We have intentionally **rejected** clipping for the following scientific reasons:

1. **Falsification of Ground Truth:** If a laboratory soil sample in Kalaburagi has $390\text{ kg/ha K}$, clipping it to $236.77\text{ kg/ha}$ fabricates artificial data and misrepresents physical soil reality.
2. **False Precision:** Min-max scaling raw soil test values into the training distribution assumes a linear equivalence between native soil test reserves and crop fertilizer requirements that does not exist in nature.
3. **Engineering Transparency:** It is far better to pass the true, unadulterated field values into the model, record the prediction faithfully, and flag the out-of-distribution status clearly in metadata than to obscure the boundary condition with artificial numerical manipulation.

---

## 5. Out-of-Distribution (OOD) Detection Architecture

The backend pipeline in `backend/predict_api.py` implements automated OOD detection prior to model execution:

```python
TRAINING_FEATURE_RANGES = {
    "N": {"min": 5.53, "max": 153.79, "unit": "kg/ha"},
    "P": {"min": 3.30, "max": 177.91, "unit": "kg/ha"},
    "K": {"min": 3.54, "max": 236.77, "unit": "kg/ha"},
    "temperature": {"min": 11.54, "max": 40.50, "unit": "°C"},
    "humidity": {"min": 1.76, "max": 100.00, "unit": "%"},
    "ph": {"min": 4.90, "max": 7.76, "unit": "scale (0-14)"},
    "rainfall": {"min": 7.39, "max": 315.58, "unit": "mm"},
}
```

### Detection Logic:
1. Every input feature is evaluated against `[min, max]`.
2. Any violating feature is collected into `npk_ood_features` and `all_ood_features`.
3. If $N, P,$ or $K$ exceeds the bounds:
   - `npk_out_of_training_range` is set to `True`.
   - `ood_warning` issues an explicit cautionary notification:
     > *"Input features ['N', 'K'] exceed the empirical training dataset bounds (Training ranges: N=[5.5-153.8], P=[3.3-177.9], K=[3.5-236.8] kg/ha). The Random Forest model is extrapolating outside its observed training distribution; predictions represent algorithmic extrapolation and should be interpreted with caution."*
4. The prediction payload returns the reference bounds (`training_ranges`) alongside the raw inputs for full auditability.

---

## 6. Ten-Location Karnataka Test Matrix (Verification Results)

The table below records the execution results across the 10 representative locations using the pure, unclipped Random Forest model (`models/crop_model.pkl`):

| Location | N / P / K (kg/ha) | OOD Status | OOD Features | Temp | Hum | Rain | pH (Fallback?) | Soil Type (Conf %) | Top 3 Crop Predictions (Raw Model Probabilities) |
|---|---|---|---|---|---|---|---|---|---|
| **Bengaluru** (`12.9716, 77.5946`) | **249.7 / 46.8 / 180.4** | `True` | `['N']` | 28.3°C | 61% | 0.7 mm | 5.80 (`YES`) | Sandy (34.4%) | 1. Grapes (30.5%)<br>2. Muskmelon (22.5%)<br>3. Maize (17.5%) |
| **Mysuru** (`12.2958, 76.6394`) | **369.7 / 9.2 / 265.6** | `True` | `['N', 'K']` | 30.3°C | 53% | 0.0 mm | 5.80 (`YES`) | Loamy (55.8%) | 1. Muskmelon (28.5%)<br>2. Grapes (26.5%)<br>3. Maize (21.5%) |
| **Hassan** (`13.0068, 76.1004`) | **369.7 / 9.2 / 265.6** | `True` | `['N', 'K']` | 28.3°C | 56% | 0.2 mm | 5.80 (`YES`) | Sandy (56.8%) | 1. Muskmelon (41.0%)<br>2. Grapes (20.5%)<br>3. Maize (20.0%) |
| **Kodagu / Madikeri** (`12.4244, 75.7382`) | **369.7 / 9.2 / 265.6** | `True` | `['N', 'K']` | 27.4°C | 48% | 0.0 mm | 5.80 (`YES`) | Loamy (77.9%) | 1. Grapes (28.0%)<br>2. Muskmelon (27.5%)<br>3. Maize (24.0%) |
| **Shivamogga** (`13.9299, 75.5681`) | **369.7 / 9.2 / 265.6** | `True` | `['N', 'K']` | 29.8°C | 57% | 0.4 mm | 5.80 (`YES`) | Loamy (86.6%) | 1. Muskmelon (28.5%)<br>2. Grapes (25.5%)<br>3. Maize (23.5%) |
| **Mangaluru** (`12.9141, 74.8560`) | **369.7 / 9.2 / 265.6** | `True` | `['N', 'K']` | 28.7°C | 67% | 0.0 mm | 5.80 (`YES`) | Sandy (89.1%) | 1. Muskmelon (41.0%)<br>2. Maize (21.5%)<br>3. Grapes (20.5%) |
| **Belagavi** (`15.8497, 74.4977`) | **202.0 / 18.9 / 347.0** | `True` | `['N', 'K']` | 27.1°C | 69% | 1.5 mm | 5.80 (`YES`) | Black (76.0%) | 1. Grapes (27.5%)<br>2. Muskmelon (24.0%)<br>3. Watermelon (14.0%) |
| **Dharwad** (`15.4589, 75.0078`) | **202.0 / 18.9 / 347.0** | `True` | `['N', 'K']` | 27.8°C | 72% | 1.2 mm | 5.80 (`YES`) | Black (70.6%) | 1. Grapes (28.0%)<br>2. Muskmelon (27.5%)<br>3. Watermelon (19.5%) |
| **Raichur** (`16.2120, 77.3439`) | **203.6 / 30.9 / 346.4** | `True` | `['N', 'K']` | 32.9°C | 42% | 0.0 mm | 5.80 (`YES`) | Black (38.4%) | 1. Grapes (26.0%)<br>2. Muskmelon (18.0%)<br>3. Maize (10.0%) |
| **Kalaburagi** (`17.3297, 76.8343`) | **250.0 / 75.0 / 390.0** | `True` | `['N', 'K']` | 32.2°C | 37% | 0.0 mm | 5.80 (`YES`) | Black (79.4%) | 1. Grapes (27.5%)<br>2. Maize (17.0%)<br>3. Banana (14.5%) |

---

## 7. Model Behavior & Identified Limitations

### A. The Extrapolation Satiation Effect
Because the Random Forest classifier splits on axis-aligned orthogonal boundaries:
- Any test input with $K > 236.77\text{ kg/ha}$ triggers the outermost right leaf node (`K > 150`).
- Because Grapes and Apple were the only crops in the training dataset with high potassium requirements, the model's voting trees allocate substantial weight to Grapes.
- **Crucial Academic Caveat:** This does **not** indicate that Grapes is the ideal crop for all Karnataka vertisols; rather, it demonstrates that a decision-tree model cannot extrapolate beyond its training boundaries.

### B. Difference Between Accepting an OOD Value and Validating a Prediction
- **Accepting an OOD Value:** An engineering pipeline decision to ensure that legitimate, real-world data is not arbitrarily rejected or silenced.
- **Validating an OOD Prediction:** A scientific assertion that the model's prediction is accurate. **We do NOT claim that OOD predictions are validated.** When $N$ or $K$ exceeds the training distribution, the prediction is unvalidated algorithmic extrapolation.

### C. Limitations to be Declared in Academic Defense:
1. The Random Forest model was trained on the benchmark 23-crop dataset where N/P/K represents crop nutrient demand rather than native soil test stock.
2. In the absence of a Soil Test Crop Response (STCR) conversion equation, native soil test values saturate the high-potassium and high-nitrogen tree branches.
3. Regional proxies for Kodagu and Mangaluru currently use Hassan baseline values, which do not reflect coastal soil leaching or high-altitude organic laterites.
4. SoilGrids pH frequently falls back to regional defaults ($5.80$) due to server timeouts and urban/sealed surface masking.

---

## 8. Verification Commands

```powershell
# Run the complete test suite verifying OOD detection across 10 locations
.\.venv\Scripts\python.exe backend/test_phase7_locations.py
```
