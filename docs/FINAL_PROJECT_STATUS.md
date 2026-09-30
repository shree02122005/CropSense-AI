# CropSense AI — Final Project Status & Architecture Report

**Document Version:** 1.0  
**Phase:** 10 — Final Validation & Project Freeze  
**System:** CropSense AI (Precision Agricultural Advisory Platform)  
**Date:** September 2026  
**Status:** Validated, Hardened, and Demonstration-Ready  

---

## A. Project Overview

**CropSense AI** is a full-stack, AI-powered agricultural decision support system designed to assist farmers and agronomists in selecting optimal crops based on multi-modal environmental telemetry. The platform unifies:
1. **Computer Vision (MobileNetV2 Deep Learning):** Classifies uploaded soil photographs into 5 distinct agronomic soil types (`black`, `clay`, `loamy`, `red`, `sandy`) with out-of-domain non-soil rejection.
2. **Automated Geolocation & Telemetry Ingestion:** Derives live weather (temperature, humidity, rainfall) from the OpenWeather API and surface soil pH from the ISRIC SoilGrids 2.0 REST API.
3. **Dynamic Soil Macronutrient Mapping:** Resolves real-world available Nitrogen ($N$), Phosphorus ($P$), and Potassium ($K$) reserves via geodesic Haversine distance from peer-reviewed Karnataka agricultural university datasets.
4. **Machine Learning Recommendation Engine:** Evaluates a strict 8-feature agronomic vector through an ensemble Random Forest classifier ($200$ estimators) to recommend top-3 crops with confidence scores, market yield, profit margins, and water requirements.
5. **Out-of-Distribution (OOD) Diagnostics:** Transparently identifies when field nutrient inputs exceed training distribution bounds and tags predictions as algorithmic extrapolation rather than claiming false agronomic validation.

---

## B. Final System Architecture

```
                                  [USER BROWSER / CLIENT]
                               React 18 Single Page Application
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │  Multipart Form-Data (Image + GPS Lat / Lon)  │
                      ▼                                               ▼
              [FastAPI BACKEND]                                [React UI]
           Uvicorn Server (Port 8000)                   Framer Motion / Glassmorphism
                      │                                               ▲
     ┌────────────────┴────────────────┐                              │
     ▼                                 ▼                              │
[Soil Image Pipeline]         [Telemetry Pipeline]                    │
MobileNetV2 CNN (224x224)     ├── OpenWeather API (Temp, Hum, Rain)   │
Rejection Filters (Blur/Mask) ├── ISRIC SoilGrids 2.0 API (pH, SOC)   │
Outputs:                      └── Haversine Lookup (Published N,P,K)  │
• soil_type                                                           │
• soil_confidence                              │                      │
• soil_type_encoded                            │                      │
     │                                         │                      │
     └─────────────────┬───────────────────────┘                      │
                       ▼                                              │
          [OOD Detection Engine]                                      │
          Evaluates [N, P, K, Temp, Hum, pH, Rain]                    │
          against Phase 6 Training Dataset Bounds                     │
                       │                                              │
                       ▼                                              │
           [Strict 8-Feature Vector]                                  │
     [N, P, K, Temp, Humidity, pH, Rainfall, Soil_Enc]                 │
                       │                                              │
                       ▼                                              │
          [Random Forest Classifier]                                  │
           200 Trees (crop_model.pkl)                                 │
                       │                                              │
                       ▼                                              │
     [Structured JSON Response Payload] ──────────────────────────────┘
     • Soil Classification & Confidence
     • Live Weather & Soil pH (with Fallback flags)
     • NPK Profile & District Source Provenance
     • OOD Warning Banner & Violating Features List
     • Top-3 Ranked Crop Cards (Yield, Profit, Water Need)
```

---

## C. Frontend Architecture

- **Technology Stack:** React 18 (`react`, `react-dom`, `react-scripts`), Framer Motion (micro-animations), Lucide React (vector iconography), Axios.
- **Styling System:** Handcrafted Vanilla CSS design system ([frontend/src/index.css](file:///c:/Users/shree/Downloads/major-project-demo1/frontend/src/index.css)) featuring tailored HSL dark green/slate color palettes, smooth gradient transitions, and responsive grid layouts.
- **Key Views:**
  - `HeroPage.js`: System landing presentation with workflow introduction.
  - `AnalysisPage.js`: GPS location detection and drag-and-drop soil photo upload interface.
  - `ResultPage.js`: Interactive results dashboard displaying soil cards, NPK badges, OOD warning notice, environmental metrics, and top-3 crop cards.
  - `CropComparisonDashboard.js`: Side-by-side comparative analysis of recommended crops.
  - `HistoryPage.js`: Historical query audit log with search, filtering, and summary statistics.
- **Export Utility ([frontend/src/reportUtils.js](file:///c:/Users/shree/Downloads/major-project-demo1/frontend/src/reportUtils.js)):** Generates formatted HTML/PDF reports containing complete soil, weather, NPK provenance, OOD notice, and crop recommendations.

---

## D. Backend Architecture

- **Framework:** FastAPI (`0.111.0`) running on Uvicorn ASGI server ([backend/main.py](file:///c:/Users/shree/Downloads/major-project-demo1/backend/main.py)).
- **Orchestration:** [backend/predict_api.py](file:///c:/Users/shree/Downloads/major-project-demo1/backend/predict_api.py) runs concurrent asynchronous I/O (`asyncio.gather`) for atmospheric and soil endpoints.
- **DLL Conflict Prevention:** Strictly imports `tensorflow` before `sklearn`/`joblib` to prevent the Windows OpenMP `_pywrap_tensorflow_common.dll` `0x45A` initialization crash.
- **REST Endpoints:**
  - `GET /`: Health check and API service status.
  - `GET /history`: Retrieves logged prediction queries.
  - `GET /history/stats`: Returns aggregated query metrics.
  - `GET /history/soil-types`: Returns unique soil types logged in history.
  - `POST /predict`: Main inference endpoint accepting multipart image and coordinates.

---

## E. Soil CNN Subsystem

- **Model File:** [models/soil_cnn_model.keras](file:///c:/Users/shree/Downloads/major-project-demo1/models/soil_cnn_model.keras) (native Keras format, with `.h5` and `.pkl` fallback compatibility).
- **Architecture:** MobileNetV2 base (frozen feature extractor) with GlobalAveragePooling2D, Dense(256), BatchNormalization, Dropout(0.5), Dense(128), Dropout(0.3), and Dense(5, softmax).
- **Training Data:** 250 authentic field photographs (200 train, 50 test) across 5 classes (`black`, `clay`, `loamy`, `red`, `sandy`).
- **Validation Accuracy:** **82.5%** on genuine test photographs.
- **Rejection Heuristics:** Non-soil images, blurry uploads (Laplacian variance $< 50$), and low-confidence predictions ($< 30\%$) are rejected with informative HTTP 400 errors.

---

## F. Crop Recommendation Model

- **Model File:** [models/crop_model.pkl](file:///c:/Users/shree/Downloads/major-project-demo1/models/crop_model.pkl).
- **Algorithm:** `RandomForestClassifier(n_estimators=200, random_state=42)`.
- **Holdout Validation Performance (Phase 6 Baseline):**
  - **Accuracy:** **93.04%**
  - **Macro Precision:** **93.58%**
  - **Macro Recall:** **93.04%**
  - **Macro F1-Score:** **93.00%**
- **Input Features (Strict Positional Order):**
  1. `N` (Available Nitrogen, kg/ha)
  2. `P` (Available Phosphorus, kg/ha)
  3. `K` (Available Potassium, kg/ha)
  4. `temperature` (°C)
  5. `humidity` (%)
  6. `ph` (pH scale 0–14)
  7. `rainfall` (mm)
  8. `soil_type_encoded` (integer 0–4: black=0, clay=1, loamy=2, red=3, sandy=4)
- **Output:** Exact probabilities across 23 agricultural crop classes.

---

## G. NPK Data Pipeline

- **Database:** [data/karnataka_main_places_npk_project_ready_v1.csv](file:///c:/Users/shree/Downloads/major-project-demo1/data/karnataka_main_places_npk_project_ready_v1.csv) containing 32 documented Karnataka profiles compiled from ICAR, UAS Dharwad, UAS Bangalore, and KVK publications.
- **Lookup Method ([backend/npk_lookup.py](file:///c:/Users/shree/Downloads/major-project-demo1/backend/npk_lookup.py)):** Geodesic great-circle Haversine distance search.
- **Provenance Tracking:** Distinguishes between `published_measured` (e.g., Bengaluru, Hassan, Dharwad, Kalaburagi) and `regional_proxy` (nearest agro-climatic baseline for unmapped districts).
- **Unclipped Integrity:** Field values such as $N=250.0, K=390.0\text{ kg/ha}$ pass into the model without artificial numerical clipping.

---

## H. Weather Pipeline

- **Provider:** OpenWeather OneCall API (`https://api.openweathermap.org/data/2.5/weather`).
- **Telemetry:** Ingests live temperature, relative humidity, and 1-hour precipitation.
- **Fault Tolerance:** If network access fails or coordinates fall outside weather station coverage, `_weather_fallback()` provides latitude-calibrated agro-climatic defaults ($28.0^\circ\text{C}, 75\%, 110\text{ mm}$ for tropical coordinates) without interrupting pipeline execution.

---

## I. pH Pipeline

- **Provider:** ISRIC SoilGrids 2.0 REST API (`https://rest.isric.org/soilgrids/v2.0/properties/query`).
- **Telemetry:** Depth layer `0-5cm` mean pH ($H_2O$) and Soil Organic Carbon (SOC).
- **Transparency on Fallback:** Urban coordinate nulls (sealed surface masks) or foreign server timeouts (>12s) trigger transparent fallback to regional baseline pH ($5.80$), tagged with `ph_is_fallback: True` and explicit audit descriptions.

---

## J. Out-of-Distribution (OOD) Detection

- **Mechanism:** Evaluates incoming inputs against empirical training boundaries:
  - $N \in [5.53, 153.79]\text{ kg/ha}$
  - $P \in [3.30, 177.91]\text{ kg/ha}$
  - $K \in [3.54, 236.77]\text{ kg/ha}$
- **Payload Metadata:**
  - `npk_out_of_training_range`: Boolean indicator.
  - `npk_ood_features`: List of violating macronutrient features (e.g., `["N", "K"]`).
  - `ood_warning`: Explains that inputs exceed empirical training limits and model outputs represent mathematical tree extrapolation.
  - `training_ranges`: Benchmark minimum/maximum bounds returned alongside prediction.

---

## K. API Endpoints Specification

| Method | Endpoint | Description | Input Parameters | Output Payload |
|---|---|---|---|---|
| `GET` | `/` | Health check & service banner | None | `{"status": "ok", "message": "..."}` |
| `GET` | `/history` | Query audit log | Query: `limit`, `soil_type`, `search` | `{"history": [...]}` |
| `GET` | `/history/stats` | Aggregated metrics | None | `{"total_predictions": N, "unique_locations": N, ...}` |
| `GET` | `/history/soil-types` | Distinct logged soil types | None | `{"soil_types": [...]}` |
| `POST` | `/predict` | Full prediction pipeline | Form: `image` (JPG/PNG), `latitude`, `longitude` | Full prediction JSON (23 fields) |

---

## L. Summary of Testing Completed

1. **Model Holdout Validation (Phase 6):** 93.04% accuracy on 230 holdout samples ([MODEL_BASELINE_RESULTS.md](file:///c:/Users/shree/Downloads/major-project-demo1/MODEL_BASELINE_RESULTS.md)).
2. **Phase 8 Location Testing:** 10 diverse Karnataka locations executed and audited ([LOCATION_TEST_RESULTS.md](file:///c:/Users/shree/Downloads/major-project-demo1/LOCATION_TEST_RESULTS.md)).
3. **Phase 9 Comprehensive Stability Suite:** 10 core testing areas (imports, CNN, NPK, weather fallback, pH fallback, OOD, RF, edge cases, regression, performance) passed with 100% success ([PHASE9_FINAL_INTEGRATION_REPORT.md](file:///c:/Users/shree/Downloads/major-project-demo1/PHASE9_FINAL_INTEGRATION_REPORT.md)).
4. **Phase 10 Final Audit:** 13-step end-to-end pipeline, API contract, and report generation validated ([PHASE10_FINAL_REPORT.md](file:///c:/Users/shree/Downloads/major-project-demo1/PHASE10_FINAL_REPORT.md)).

---

## M. Clear Distinction of Model Results & Identified Limitations

### 1. Model Validation on Benchmark Data (Validated):
On the held-out test split of the 23-crop dataset, the Random Forest model achieves **93.04% accuracy**. This demonstrates that *within its training domain*, the classifier accurately maps combinations of climate and nutrient requirements to crop labels.

### 2. Real Karnataka Location Testing (Empirical Observation):
When real-world Karnataka soil values are supplied, the backend runs completely and stably without software errors.

### 3. OOD Algorithmic Predictions (NOT Agronomically Validated):
Because native Karnataka vertisols contain $260–390\text{ kg/ha}$ exchangeable potassium (exceeding the training maximum of $236.77\text{ kg/ha}$), the decision trees enter **extrapolation satiation**. Every split on potassium branches unconditionally into the extreme right leaf node, causing the model to allocate substantial probability to **Grapes** and **Muskmelon**.
> **CRITICAL SCIENTIFIC NOTICE:** Predictions where $N$ or $K$ is flagged as OOD represent **algorithmic decision-tree extrapolation**. They are **not** agronomically validated field recommendations. This is an identified research boundary resulting from the semantic gap between crop fertilizer requirements and native soil test reserves.

---

## N. How to Run the Project

```powershell
# 1. Start Backend Server (Port 8000)
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Start Frontend Development Server (Port 3000)
cd frontend
npm start
```

---

## O. How to Perform a Demo Prediction

1. Open `http://localhost:3000` in the browser.
2. Click **Get Started** or **Analyze Soil**.
3. Click **Detect Location** (or enter Bengaluru coordinates: `12.9716, 77.5946`).
4. Upload an authentic soil photo (e.g., from `cnn/dataset/test/red/test_red_000.jpg` or `cnn/dataset/test/black/test_black_000.jpg`).
5. Click **Begin Soil Analysis**.
6. Observe the animated multi-stage analysis:
   - Soil CNN classification and confidence score
   - Live weather parameters and SoilGrids pH
   - NPK macronutrients and district provenance badge
   - **Out-of-Distribution notice banner** indicating training boundary extrapolation
   - Top-3 recommended crop cards with market yield and profit ratings
7. Click **Print Report** or **Download PDF** to inspect the generated agronomic summary.
