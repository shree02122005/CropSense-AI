# CropSense AI

**CropSense AI** is an intelligent, full-stack agricultural decision-support platform designed to empower farmers, agronomists, and researchers. By combining computer vision with multi-source environmental telemetry, CropSense AI analyzes surface soil photographs, district-level soil nutrient surveys, live atmospheric weather, and satellite depth pH to recommend agronomically viable crops with high precision.

---

## Features

- **Soil Classification (Computer Vision):** Transfer-learning MobileNetV2 deep neural network classifying soil images into 5 major classes (`black`, `clay`, `loamy`, `red`, `sandy`) with domain validation against blur, extreme lighting, and non-soil graphics.
- **Location-Aware Environmental Telemetry:** Automated GPS matching against published Agricultural University soil fertility surveys across Karnataka districts.
- **N/P/K Integration:** Dynamic retrieval of authentic soil available Nitrogen (N), Phosphorus (P), and Potassium (K) profiles based on geographic proximity.
- **Real-Time Weather Ingestion:** Ingestion of ambient temperature, relative humidity, and seasonal rainfall via OpenWeatherMap API with automatic resilient fallbacks.
- **Soil pH Analysis:** Surface depth soil pH (0–30 cm) retrieved from ISRIC SoilGrids 2.0 with agro-climatic regional fallback mechanisms.
- **Random Forest Crop Prediction (Production):** High-performing multi-class ensemble predicting the top 3 ranked candidate crops accompanied by indicative confidence scores.
- **XGBoost Academic Comparison (Experimental):** Standalone gradient boosting benchmark model for comparative evaluation and academic defense.
- **Crop Comparison Dashboard:** Interactive side-by-side comparison matrix evaluating water needs, growing seasons, anticipated yield ranges, and commercial market rates.
- **Prediction History & Analytics:** Local query persistence with filtering by soil type and interactive analytics.
- **PDF Report Generation:** Professional client-side downloadable agronomic advisory report (PDF) powered by jsPDF and autoTable.
- **Out-of-Distribution (OOD) Detection:** Transparent boundary verification flagging when local soil nutrients exceed baseline training distributions without artificial clipping or multiplier tampering.

---

## Architecture

The system coordinates computer vision, geospatial lookups, external REST telemetry, and ensemble machine learning into a unified prediction pipeline:

```
[ Surface Soil Photograph ]
           │
           ▼
[ Soil MobileNetV2 CNN ] ────► [ Soil Type: Black / Clay / Loamy / Red / Sandy ]
                                                  │
[ GPS Latitude / Longitude ]                      │
           │                                      │
           ├──► [ Haversine NPK Lookup ] ─────────┼──► [ N, P, K (kg/ha) ]
           ├──► [ OpenWeatherMap API ]   ─────────┼──► [ Temperature, Humidity, Rain ]
           └──► [ ISRIC SoilGrids 2.0 ]  ─────────┴──► [ Soil pH (0-14) ]
                                                           │
                                                           ▼
                                         [ 8-Dimensional Feature Vector ]
                                      [N, P, K, Temp, Hum, pH, Rain, Soil_Enc]
                                                           │
                                         ┌─────────────────┴─────────────────┐
                                         ▼                                   ▼
                            [ OOD Detection Engine ]              [ Random Forest Model ]
                                         │                                   │
                                         ▼                                   ▼
                            [ Out-of-Range Alerts ]             [ Top-3 Crop Predictions ]
                                                                             │
                                                                             ▼
                                                                [ CropSense AI Dashboard ]
```

---

## Machine Learning Models

CropSense AI evaluates two distinct machine learning algorithms trained on the identical holdout split from the project dataset (`datasets/Crop_recommendation_clean.csv`, 80/20 stratified split, `random_state=42`, zero data leakage):

### Production Model: Random Forest Classifier
- **Model File:** `models/crop_model.pkl` (13.52 MB)
- **Framework:** `scikit-learn` (`RandomForestClassifier`, 200 trees, `gini` criterion)
- **Role:** **Active Deployed Production Engine** powering the live API and web dashboard.
- **Measured Evaluation Results (Holdout Test Split, n=230):**
  - **Overall Accuracy:** **93.04%** (214 / 230 correct)
  - **Macro Precision:** **93.22%**
  - **Macro Recall:** **93.04%**
  - **Macro F1-Score:** **93.00%**
  - **Weighted F1-Score:** **93.00%**
- **Inference Latency:** 0.275 ms / sample

### Experimental Model: XGBoost Classifier
- **Model File:** `models/crop_model_xgboost_demo.pkl` (2.17 MB)
- **Framework:** `xgboost` (`XGBClassifier`, 100 boosting rounds, depth 4, learning rate 0.1)
- **Role:** **Academic Demonstration & Comparison Model** (strictly decoupled from production).
- **Measured Evaluation Results (Holdout Test Split, n=230):**
  - **Overall Accuracy:** **90.87%** (209 / 230 correct)
  - **Macro Precision:** **91.21%**
  - **Macro Recall:** **90.87%**
  - **Macro F1-Score:** **90.76%**
  - **Weighted F1-Score:** **90.76%**
  - **Inference Latency:** 0.034 ms / sample

*Note: All performance metrics are empirically measured holdout evaluation results on the clean project dataset.*

---

## Important Agronomic Limitation: NPK Semantic Mismatch & OOD Behavior

> [!WARNING]
> **Academic & Agronomic Disclaimer:**  
> In accordance with scientific integrity and transparent engineering standards:
> 1. **Semantic Distribution Shift:** The training dataset reflects international agro-ecological trial ranges (N: 5.5–153.8, P: 3.3–177.9, K: 3.5–236.8 kg/ha). Certain Karnataka districts feature natural soil test values (e.g. Mysuru N=369.7, Kalaburagi K=390.0 kg/ha) that lie outside these boundaries.
> 2. **No Artificial Data Tampering:** The system does **not** artificially normalize, scale, clip, or apply arbitrary multipliers to force values into range.
> 3. **Out-of-Distribution (OOD) Transparency:** When input features exceed the training boundaries, the system explicitly flags `ood_detected: true`, identifies the specific out-of-range nutrient dimensions, and alerts the user.
> 4. **Decision Support Only:** Predictions generated under OOD conditions are mathematical model outputs and must **not** be interpreted as certified agronomic prescriptions without local extension verification.

---

## Installation & Quick Start

For complete prerequisite checks, API key setup, and troubleshooting, consult [docs/RUN_INSTRUCTIONS.md](docs/RUN_INSTRUCTIONS.md).

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm 9+

### 2. Backend Setup
```bash
# From project root
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example backend/.env
# Edit backend/.env with your free OpenWeatherMap API key

# Start FastAPI backend server
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
# Open a second terminal from project root
cd frontend

# Install dependencies
npm install

# Start React development server
npm start
```
The application will launch automatically at `http://localhost:3000`.

---

## Project Structure

```
CropSense-AI/
├── README.md                           ← Main project documentation
├── requirements.txt                    ← Root Python dependencies
├── .gitignore                          ← Git exclusion rules
├── .env.example                        ← Template environment configuration
├── Dockerfile.backend                  ← Containerization definition
│
├── backend/                            ← FastAPI application & ML pipelines
│   ├── main.py                         ← REST API routes & middleware
│   ├── predict_api.py                  ← Core hybrid prediction pipeline
│   ├── history.py                      ← Prediction history persistence
│   ├── npk_lookup.py                   ← Haversine nearest-neighbor NPK lookup
│   ├── utils.py                        ← Agronomic crop metadata & pricing
│   ├── train_model.py                  ← Legacy model training reference
│   ├── retrain_and_evaluate.py         ← Production Random Forest training
│   ├── train_xgboost_demo.py           ← Academic XGBoost demo training
│   └── compare_models.py               ← Model benchmark runner
│
├── frontend/                           ← React 18 user interface
│   ├── package.json                    ← Node.js manifest & dependencies
│   ├── src/
│   │   ├── App.js                      ← View routing & application state
│   │   ├── index.css                   ← Theme tokens & hero styling
│   │   ├── reportUtils.js              ← jsPDF report generation engine
│   │   ├── assets/crop-field-bg.png    ← Homepage hero background photograph
│   │   └── pages/                      ← Page components (Hero, Option, Analysis, Result, etc.)
│   └── public/                         ← Static HTML template
│
├── cnn/                                ← Soil classification neural network
│   ├── predict_soil.py                 ← Inference engine & image domain validation
│   ├── train_cnn.py                    ← MobileNetV2 fine-tuning pipeline
│   └── dataset/                        ← Genuine soil image datasets (train & test)
│
├── datasets/                           ← Tabular ML training datasets
│   ├── Crop_recommendation_clean.csv   ← Canonical 1150-sample clean dataset
│   └── Crop_recommendation.csv         ← Original 2200-sample baseline dataset
│
├── data/                               ← Runtime databases & reference maps
│   ├── karnataka_main_places_npk_project_ready_v1.csv ← Published Karnataka NPK survey
│   └── predictions_history.json        ← Runtime user prediction history
│
├── models/                             ← Trained model binaries
│   ├── crop_model.pkl                  ← Production Random Forest (13.52 MB)
│   ├── crop_model_xgboost_demo.pkl     ← Academic XGBoost demo (2.17 MB)
│   ├── soil_cnn_model.keras            ← Production MobileNetV2 CNN (13.98 MB)
│   ├── soil_cnn_model.h5               ← Multi-tier H5 fallback weights
│   └── soil_cnn_model.pkl              ← Scikit-learn color centroid fallback
│
├── docs/                               ← Comprehensive documentation repository
│   ├── MODEL_FILES.md                  ← Detailed model specifications & roles
│   ├── DATASET_FILES.md                ← Dataset provenance & field documentation
│   ├── RUN_INSTRUCTIONS.md             ← Step-by-step setup and startup guide
│   ├── MODEL_BASELINE_RESULTS.md       ← Phase 6 Random Forest holdout metrics
│   ├── XGBOOST_DEMO_COMPARISON.md      ← Side-by-side RF vs XGBoost benchmark
│   ├── XGBOOST_DEMO_README.md          ← XGBoost reproduction commands
│   ├── LOCATION_TEST_RESULTS.md        ← Empirical Karnataka field location tests
│   ├── NPK_INFERENCE_COMPATIBILITY.md  ← Scientific analysis of NPK distribution shifts
│   ├── VIVA_DEMO_NOTES.md              ← Comprehensive viva demonstration & defense guide
│   └── assets/                         ← High-resolution benchmark charts & galleries
│
├── tests/                              ← Automated test suites & verification scripts
│   ├── test_phase10_validation.py      ← Demo readiness & full API contract audit
│   ├── test_phase9_full_regression.py  ← 10-location regression test against baseline
│   ├── test_phase9_comprehensive.py    ← 10-domain stability & stress test suite
│   ├── test_phase8_locations.py        ← End-to-end Karnataka location test suite
│   └── results/                        ← Machine-readable JSON test output logs
│
└── archive/                            ← Historical preservation & recovery snapshots
    └── backups/                        ← Milestone backups (Original, Phase 9, Phase 10, etc.)
```

---

## Key Documentation Index

All technical documents are cataloged in the [`docs/`](docs/) directory:

- **Setup & Execution:** [docs/RUN_INSTRUCTIONS.md](docs/RUN_INSTRUCTIONS.md)
- **Model Technical Specs:** [docs/MODEL_FILES.md](docs/MODEL_FILES.md)
- **Dataset Provenance & Schema:** [docs/DATASET_FILES.md](docs/DATASET_FILES.md)
- **Random Forest Baseline Metrics:** [docs/MODEL_BASELINE_RESULTS.md](docs/MODEL_BASELINE_RESULTS.md)
- **XGBoost Demonstration Benchmark:** [docs/XGBOOST_DEMO_COMPARISON.md](docs/XGBOOST_DEMO_COMPARISON.md)
- **XGBoost Reproduction Guide:** [docs/XGBOOST_DEMO_README.md](docs/XGBOOST_DEMO_README.md)
- **Karnataka Regional Testing:** [docs/LOCATION_TEST_RESULTS.md](docs/LOCATION_TEST_RESULTS.md)
- **NPK Semantic Mismatch Analysis:** [docs/NPK_INFERENCE_COMPATIBILITY.md](docs/NPK_INFERENCE_COMPATIBILITY.md)
- **Viva & Examiner Defense Notes:** [docs/VIVA_DEMO_NOTES.md](docs/VIVA_DEMO_NOTES.md)
- **Project Completion Status:** [docs/FINAL_PROJECT_STATUS.md](docs/FINAL_PROJECT_STATUS.md)

---

## License & Academic Citation

Developed as an academic major engineering project. Licensed for educational and research evaluation under the MIT License.
