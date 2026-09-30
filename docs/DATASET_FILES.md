# CropSense AI — Dataset Files Documentation

This document describes all tabular datasets and spatial reference files used in CropSense AI across `datasets/` and `data/`.

---

## 1. Summary of Dataset Files

| File Path | Records | Features | Target / Purpose | Role |
|:---|:---:|:---:|:---|:---:|
| `datasets/Crop_recommendation_clean.csv` | 1,150 | 8 features | 23 crops (50/class) | **Canonical Training Dataset** |
| `datasets/Crop_recommendation.csv` | 2,200 | 7 features | 22 crops (100/class) | **Baseline Legacy Dataset** |
| `data/karnataka_main_places_npk_project_ready_v1.csv` | 31 districts | Lat, Lon, N, P, K | Spatial Soil Fertility | **Canonical NPK Reference** |
| `data/predictions_history.json` | Dynamic | Complete telemetry | Persistence Log | **Runtime Query History** |

---

## 2. Canonical Training Dataset

- **Path:** `datasets/Crop_recommendation_clean.csv`
- **File Size:** 108.68 KB
- **Rows:** 1,150 (exactly 50 balanced rows per class across 23 crop classes)
- **Features (8 input columns):**
  1. `N` (kg/ha): Available soil nitrogen (5.53 – 153.79 kg/ha).
  2. `P` (kg/ha): Available soil phosphorus (3.30 – 177.91 kg/ha).
  3. `K` (kg/ha): Available soil potassium (3.54 – 236.77 kg/ha).
  4. `temperature` (°C): Ambient temperature (11.54 – 40.50 °C).
  5. `humidity` (%): Relative atmospheric humidity (1.76 – 100.00%).
  6. `ph`: Soil pH (4.90 – 7.76).
  7. `rainfall` (mm): Mean seasonal precipitation (7.39 – 315.58 mm).
  8. `soil_type_encoded` (int 0–4): 0=black, 1=clay, 2=loamy, 3=red, 4=sandy.
- **Target Column:** `label` (string name of the optimal crop).
- **Provenance & Cleaning Rationale:**
  - Resolved the legacy defect where red soil had 0 training samples.
  - Introduced balanced red soil profiles for appropriate crops (ragi/finger millet, pulses, groundnut, cotton).
  - Cleaned extreme unphysical outliers while preserving natural biological variation.
  - Used for training both the production Random Forest model and the demo XGBoost model.

---

## 3. Legacy Baseline Dataset

- **Path:** `datasets/Crop_recommendation.csv`
- **File Size:** 100.42 KB
- **Rows:** 2,200 (100 samples per class across 22 classes)
- **Features (7 columns):** `N, P, K, temperature, humidity, ph, rainfall` (missing `soil_type`).
- **Role:** Preserved for academic comparison, demonstrating the necessity of Phase 5 data cleaning and soil type integration.

---

## 4. Karnataka Spatial NPK Reference Dataset

- **Path:** `data/karnataka_main_places_npk_project_ready_v1.csv`
- **File Size:** 7.69 KB
- **Content:** Agricultural University (UAS Bengaluru, UAS Dharwad, KSNUAHS Shivamogga) soil fertility surveys mapped to major district centers across Karnataka.
- **Columns:** `district, place_name, latitude, longitude, N, P, K, soil_type, source_reference`.
- **Duplicate Analysis:** A local copy exists in `backend/data/`. Both copies are byte-for-byte identical (7,695 bytes, SHA-256 matched). The copy in `backend/data/` is retained to guarantee that any script running with CWD inside `backend/` finds its candidate path without path resolution errors.

---

## 5. Runtime Prediction History

- **Path:** `data/predictions_history.json`
- **Role:** Local persistence store managed by `backend/history.py` for recording demonstration queries, enabling user query review, filtering by soil type, and export to PDF.
