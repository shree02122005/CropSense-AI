# CropSense AI — Final Project Structure & Directory Blueprint

**Document Version:** 1.0  
**Phase:** 10 — Final Validation & Project Freeze  
**Date:** September 2026  
**System:** CropSense AI (Precision Agricultural Advisory Platform)  

---

## 1. Directory Tree Overview

```text
major-project-demo1/
├── BACKUP_ORIGINAL/                  # Untouched baseline backup of all 202 original project files
├── BACKUP_PHASE9/                    # Safety backup of files modified in Phase 9 (main.py, ResultPage.js, reportUtils.js)
├── BACKUP_PHASE10/                   # Safety backup directory created for Phase 10 validation
│
├── backend/                          # FastAPI REST API & Machine Learning inference pipeline
│   ├── data/                         # Local database and dynamic lookup data
│   │   └── predictions_history.json  # JSON-persisted history of agricultural queries
│   ├── .env                          # API keys (OpenWeather API key configuration)
│   ├── history.py                    # Query logging, statistics aggregation, and history management
│   ├── main.py                       # FastAPI entry point, CORS middleware, and REST routes
│   ├── npk_lookup.py                 # Geodesic Haversine lookup against Karnataka NPK database
│   ├── predict_api.py                # Core orchestration pipeline (CNN + Weather + SoilGrids + RF + OOD)
│   ├── requirements.txt              # Production Python package dependency specifications
│   ├── train_model.py                # Original baseline model training script (preserved)
│   ├── retrain_and_evaluate.py       # Phase 6 Random Forest retraining & metric evaluation suite
│   ├── test_prediction_flow.py       # Baseline prediction unit test
│   ├── test_phase7_locations.py      # Phase 7 backend verification script
│   ├── test_phase8_locations.py      # Phase 8 10-location automated test runner
│   ├── test_phase9_comprehensive.py  # Phase 9 10-section stability and error-handling test suite
│   ├── test_phase9_full_regression.py# Phase 9 regression test suite against Phase 8 baseline
│   ├── test_phase10_validation.py    # Phase 10 final validation & 13-step demo pipeline runner
│   └── utils.py                      # Agronomic crop metadata dictionary (yield, prices, seasons, profit)
│
├── cnn/                              # Soil image classification deep learning subsystem
│   ├── dataset/                      # Dataset directories for Soil MobileNetV2 CNN
│   │   ├── train/                    # 200 authentic soil photos (40 per class: black, clay, loamy, red, sandy)
│   │   ├── test/                     # 50 authentic soil photos (10 per class)
│   │   ├── test_non_soil/            # Out-of-domain rejection test set (sky, foliage, urban, noise)
│   │   └── synthetic_baseline/       # Preserved baseline noise images from original project
│   ├── generate_sample_images.py     # Preserved original generator
│   ├── prepare_genuine_dataset.py    # Script for ingesting and organizing genuine soil photographic datasets
│   ├── predict_soil.py               # MobileNetV2 soil classifier with non-soil rejection safeguards
│   └── train_cnn.py                  # MobileNetV2 transfer learning training pipeline (82.5% val acc)
│
├── data/                             # Project-wide agricultural reference datasets
│   ├── karnataka_main_places_npk_project_ready_v1.csv  # 32 published Karnataka district NPK profiles
│   └── predictions_history.json      # Root-level query persistence
│
├── datasets/                         # Tabular datasets for crop recommendation ML model
│   ├── Crop_recommendation.csv       # Original Kaggle 2,200-row benchmark dataset
│   └── Crop_recommendation_clean.csv # Cleaned Phase 5 dataset (1,150 rows: 23 crops x 50 samples, red soil balanced)
│
├── frontend/                         # Modern React web application UI
│   ├── build/                        # Production optimized static build
│   ├── public/                       # HTML boilerplate, favicon, manifest
│   │   └── index.html                # Root HTML document
│   ├── src/                          # React components and styling
│   │   ├── pages/                    # Application views
│   │   │   ├── AnalysisPage.js       # Soil upload & coordinate selection workflow
│   │   │   ├── CropComparisonDashboard.js # Interactive multi-crop comparison dashboard
│   │   │   ├── HeroPage.js           # Modern landing page with feature cards
│   │   │   ├── HistoryPage.js        # Prediction history list, search, and statistics view
│   │   │   ├── HistoryPage.css       # History page styles
│   │   │   ├── OptionPage.js         # Mode selection navigation
│   │   │   └── ResultPage.js         # Results view with soil cards, NPK provenance, OOD notice, crops
│   │   ├── App.js                    # View routing & application state management
│   │   ├── index.css                 # Global design system (dark green/slate palette, glassmorphism)
│   │   ├── index.js                  # React DOM mount point
│   │   └── reportUtils.js            # Printable & PDF report generation utilities (with NPK & OOD notices)
│   ├── .env                          # Frontend port and backend endpoint configurations
│   ├── Dockerfile                    # Containerization specification for frontend
│   ├── package.json                  # NPM dependencies (React 18, framer-motion, lucide-react, axios)
│   └── package-lock.json             # Exact dependency lockfile
│
├── models/                           # Trained machine learning model artifacts
│   ├── crop_model.pkl                # Production Random Forest crop model (200 trees, 8 features, 23 classes)
│   ├── soil_cnn_model.keras          # Production MobileNetV2 Soil CNN (Keras native format, 82.5% val acc)
│   ├── soil_cnn_model.h5             # Production MobileNetV2 Soil CNN (HDF5 format)
│   └── soil_cnn_model.pkl            # Preserved original baseline fallback bundle
│
└── Documentation & Reports/          # Comprehensive academic and engineering reports
    ├── DATASET_DOCUMENTATION.md      # Phase 5 dataset provenance, agronomic audit & cleaning report
    ├── MODEL_BASELINE_RESULTS.md     # Phase 6 model retraining metrics, confusion matrix, and feature importances
    ├── NPK_INFERENCE_COMPATIBILITY.md# Phase 7 NPK compatibility & OOD detection documentation
    ├── LOCATION_TEST_RESULTS.md      # Phase 8 10-location Karnataka validation and root-cause analysis
    ├── PHASE9_FINAL_INTEGRATION_REPORT.md # Phase 9 stability, route fix, and regression report
    ├── PHASE10_PROJECT_STRUCTURE.md  # [This Document] Final directory and file blueprint
    ├── FINAL_PROJECT_STATUS.md       # Consolidated final system architecture and status report
    ├── VIVA_DEMO_NOTES.md            # 20 concise factual Q&A notes for college project defense
    ├── RUN_INSTRUCTIONS.md           # Step-by-step commands to install, run, and demo the system
    └── PHASE10_FINAL_REPORT.md       # Final project sign-off and completion report
```

---

## 2. Description of Major Subsystems

| Subsystem | Primary Directory | Key File | Architectural Role |
|---|---|---|---|
| **Web Frontend** | `frontend/` | `src/App.js`, `src/pages/ResultPage.js` | User interface providing soil photo upload, GPS geolocation, animated progress, OOD notifications, and PDF report downloads. |
| **Backend REST API** | `backend/` | `main.py` | FastAPI application exposing `/predict`, `/history`, and `/history/stats` endpoints with CORS and request validation. |
| **Orchestration Pipeline** | `backend/` | `predict_api.py` | Coordinates CNN inference, OpenWeather query, SoilGrids query, Haversine NPK lookup, OOD detection, and Random Forest prediction. |
| **Soil Classification** | `cnn/` | `predict_soil.py`, `train_cnn.py` | MobileNetV2 deep learning classifier recognizing 5 genuine soil classes with out-of-domain rejection heuristics. |
| **Macronutrient Lookup** | `backend/`, `data/` | `npk_lookup.py`, `karnataka_main_places_npk_project_ready_v1.csv` | Geodesic distance lookup linking coordinates to published ICAR/UAS Karnataka soil nutrient profiles. |
| **Crop Recommendation** | `models/`, `backend/` | `models/crop_model.pkl`, `predict_api.py` | 200-tree Random Forest evaluating 8 features to output top-3 crop probabilities. |
| **Archival Backups** | `BACKUP_ORIGINAL/`, `BACKUP_PHASE9/`, `BACKUP_PHASE10/` | `README_BASELINE.txt` | Complete snapshot isolation ensuring non-destructive engineering throughout all project phases. |

---

## 3. Storage and File Integrity Summary

- **Total Baseline Files Preserved:** 202 files in `BACKUP_ORIGINAL/`
- **Total Models in Production:** 2 (`crop_model.pkl` and `soil_cnn_model.keras`)
- **Total Datasets Maintained:** 3 (`Crop_recommendation.csv`, `Crop_recommendation_clean.csv`, `karnataka_main_places_npk_project_ready_v1.csv`)
- **Active Virtual Environment:** Python 3.10.11 in `.venv/`
