# CropSense AI — Project Cleanup Inventory & Classification Audit

**Audit Date:** September 2026  
**Document Purpose:** Comprehensive pre-cleanup audit and categorization of all project assets, source code, models, datasets, tests, documentation, and backups prior to GitHub staging.  
**Rule Adherence:** No files are deleted during this inventory phase. All assets are classified into standardized categories with explicit recommendations and rationales.

---

## 1. Classification Taxonomy

Each file or directory is assessed against the required decision criteria:
- **A. Required by Application:** Core runtime dependencies for FastAPI backend, CNN inference, and React frontend.
- **B. Required for Model Training:** Datasets, feature extraction, and training pipelines.
- **C. Required for Reproducibility:** Baseline scripts, test seeds, and environment configurations.
- **D. Required for Documentation:** Architecture guides, evaluation benchmarks, and viva presentation notes.
- **E. Useful Backup:** Historical milestone snapshots and rollback points.
- **F. Genuine Duplicate:** Redundant identical copies of canonical assets.
- **G. Generated / Cache / Temporary:** Compiled bytecode, runtime logs, or temporary build caches.

---

## 2. Comprehensive Inventory Table

### 2.1 Root Level Files

| File / Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `README.md` | D | Project overview and landing documentation | **Keep / Update** in root | Primary entry point for GitHub visitors and evaluators. |
| `Dockerfile.backend` | A | Backend Docker containerization specification | **Keep** in root | Enables containerized production deployment of FastAPI. |
| `audit_soil_classifier.py` | C | Standalone test script auditing soil CNN heuristic rules | **Move** to `tests/` | Belongs in tests directory; does not belong in project root. |
| `reportUtils.js` | F/C | Minimal CommonJS stub used only by `test_report_fixes.js` | **Move** to `tests/` | Outdated 1.9 KB stub. Production report code is in `frontend/src/reportUtils.js`. Kept with test script for offline testing. |
| `test_report_fixes.js` | C | Node test script verifying report generation against edge cases | **Move** to `tests/` | Belongs with automated tests in `tests/`. |
| `soil_color_palette.png` | D | Color centroid analysis visualization for soil classification | **Move** to `docs/assets/` | Technical visual documentation referenced in CNN reports. |
| `soil_texture_ranges.png` | D | Laplacian variance texture range chart across soil classes | **Move** to `docs/assets/` | Technical visual documentation for soil morphology. |
| `soil_training_gallery.png` | D | High-resolution visual gallery of genuine soil training dataset | **Move** to `docs/assets/` | Visual proof of authentic dataset collection (3.6 MB). |
| `XGBOOST_RF_COMPARISON.png` | D | Benchmark bar chart comparing Random Forest vs. XGBoost | **Move** to `docs/assets/` | Evaluator reference chart for model comparison. |
| `DATASET_DOCUMENTATION.md` | D | Full dataset provenance, cleaning, and field mappings | **Move** to `docs/` | Consolidate under `docs/` to keep repository root clean. |
| `FINAL_HERO_BACKGROUND_UPDATE.md` | D | Hero background implementation and responsive test report | **Move** to `docs/` | Phase documentation for frontend redesign. |
| `FINAL_PROJECT_STATUS.md` | D | Comprehensive summary of project achievements and architecture | **Move** to `docs/` | Primary project status artifact for academic submission. |
| `FRONTEND_REDESIGN_REPORT.md` | D | Detailed design system and UI audit documentation | **Move** to `docs/` | Frontend engineering design documentation. |
| `LOCATION_TEST_RESULTS.md` | D | Complete 10-location empirical test log across Karnataka | **Move** to `docs/` | Empirical proof of regional testing and OOD transparency. |
| `MODEL_BASELINE_RESULTS.md` | D | Phase 6 Random Forest baseline training and holdout metrics | **Move** to `docs/` | Core model evaluation baseline document. |
| `NPK_INFERENCE_COMPATIBILITY.md` | D | Scientific analysis of NPK distribution shifts and OOD detection | **Move** to `docs/` | Explains agronomic units and semantic mismatch boundaries. |
| `OPENWEATHER_AUDIT_REPORT.md` | D | OpenWeather API integration and fallback audit | **Move** to `docs/` | Telemetry pipeline documentation. |
| `OPENWEATHER_FIX_SUMMARY.md` | D | Summary of weather fallback and timeout hardening | **Move** to `docs/` | Telemetry pipeline documentation. |
| `OPENWEATHER_TECHNICAL_REFERENCE.md` | D | API reference for weather data structures | **Move** to `docs/` | Developer documentation for external telemetry. |
| `PHASE9_FINAL_INTEGRATION_REPORT.md` | D | Phase 9 system integration and stability test report | **Move** to `docs/` | System verification report. |
| `PHASE10_FINAL_REPORT.md` | D | Phase 10 demo readiness, code audit, and viva preparation report | **Move** to `docs/` | Milestone completion report. |
| `PHASE10_PROJECT_STRUCTURE.md` | D | Architectural directory map and module responsibility guide | **Move** to `docs/` | Structural project reference. |
| `RUN_INSTRUCTIONS.md` | D | Step-by-step setup, installation, and startup guide | **Move** to `docs/` | User and developer setup instructions. |
| `SOIL_CLASSIFICATION_IMPROVEMENTS.md` | D | MobileNetV2 architecture and color heuristic documentation | **Move** to `docs/` | Deep learning classifier documentation. |
| `VIVA_DEMO_NOTES.md` | D | Complete viva demonstration cheat sheet and examiner Q&A | **Move** to `docs/` | Essential academic evaluation defense notes. |
| `XGBOOST_DEMO_COMPARISON.md` | D | Technical side-by-side benchmark of RF vs. XGBoost | **Move** to `docs/` | Academic model comparison report. |
| `XGBOOST_DEMO_README.md` | D | Reproduction guide for standalone XGBoost training/comparison | **Move** to `docs/` | Model reproduction guide. |
| `phase7_backend_test_results.json` | C | Raw JSON logs of Phase 7 location tests | **Move** to `tests/results/` | Test result artifact. |
| `phase8_karnataka_test_results.json` | C | Raw JSON logs of Phase 8 Karnataka location tests | **Move** to `tests/results/` | Test result artifact used for regression baselines. |
| `phase9_regression_comparison.json` | C | Raw JSON diff comparing Phase 9 to Phase 8 | **Move** to `tests/results/` | Test result artifact. |
| `phase10_validation_results.json` | C | Raw JSON summary of Phase 10 validation checks | **Move** to `tests/results/` | Test result artifact. |

---

### 2.2 Backend Directory (`backend/`)

| File / Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `backend/main.py` | A | FastAPI application entrypoint and REST endpoints | **Keep** in `backend/` | Production server code; must remain in place. |
| `backend/predict_api.py` | A | Complete end-to-end prediction pipeline | **Keep** in `backend/` | Production prediction logic; must remain in place. |
| `backend/history.py` | A | Prediction history persistence and query logic | **Keep** in `backend/` | Production service module; must remain in place. |
| `backend/npk_lookup.py` | A | Geographic nearest-neighbor NPK lookup engine | **Keep** in `backend/` | Production NPK pipeline; must remain in place. |
| `backend/utils.py` | A | Agronomic crop profiles, pricing, and system path helpers | **Keep** in `backend/` | Production utility library; must remain in place. |
| `backend/requirements.txt` | A | Python dependencies list for backend services | **Keep** in `backend/` (and mirror to root) | Required for installing backend dependencies. |
| `backend/.env` | A/Secret | Local API keys (OpenWeather) | **Protect** via `.gitignore` / create `.env.example` | Must NOT be pushed to GitHub with active API keys. |
| `backend/train_model.py` | B/C | Historical Random Forest training script | **Keep** in `backend/` | Academic reference and baseline reproducibility. |
| `backend/retrain_and_evaluate.py` | B/C | Phase 6 production Random Forest training pipeline | **Keep** in `backend/` | Official production model training script. |
| `backend/train_xgboost_demo.py` | B/C | Standalone academic XGBoost training script | **Keep** in `backend/` | Evaluator demonstration script for model benchmarking. |
| `backend/compare_models.py` | C | Read-only model benchmark comparison runner | **Keep** in `backend/` | Evaluator demonstration runner. |
| `backend/create_clean_dataset.py` | B/C | Dataset cleaning and red-soil augmentation script | **Keep** in `backend/` | Essential for reproducing `Crop_recommendation_clean.csv`. |
| `backend/inspect_dataset.py` | C | Dataset schema and class balance inspector | **Keep** in `backend/` | Development and audit utility. |
| `backend/data/karnataka_main_places_npk_project_ready_v1.csv` | F | Local duplicate of root `data/karnataka_...csv` | **Keep** in `backend/data/` | Fallback search path in `npk_lookup.py`; keeping guarantees zero path breakage. |
| `backend/model_comparison_results.json` | C | JSON output of side-by-side RF vs XGBoost benchmark | **Move** to `tests/results/` (or keep alongside script) | Test output artifact. |
| `backend/xgboost_demo_metrics.json` | C | JSON output of XGBoost evaluation metrics | **Move** to `tests/results/` (or keep alongside script) | Test output artifact. |
| `backend/test_phase7_locations.py` | C | Phase 7 location test runner | **Move** to `tests/` | Project verification script. |
| `backend/test_phase8_locations.py` | C | Phase 8 Karnataka location validation suite | **Move** to `tests/` | Comprehensive location test suite. |
| `backend/test_phase9_comprehensive.py` | C | 10-domain comprehensive stability and integration test suite | **Move** to `tests/` | Comprehensive test suite. |
| `backend/test_phase9_full_regression.py` | C | Phase 9 regression test suite against Phase 8 baseline | **Move** to `tests/` | Regression test suite. |
| `backend/test_phase10_validation.py` | C | Phase 10 demo readiness audit suite | **Move** to `tests/` | Demo readiness audit suite. |
| `backend/test_prediction_flow.py` | C | Basic smoke test of prediction flow | **Move** to `tests/` | Smoke test script. |
| `backend/audit_fetch_weather.py` | C | Weather API diagnostic audit script | **Move** to `tests/` | Diagnostic test script. |
| `backend/audit_predictions.py` | C | Historical prediction audit script | **Move** to `tests/` | Diagnostic test script. |
| `backend/audit_soilgrids.py` | C | SoilGrids API diagnostic audit script | **Move** to `tests/` | Diagnostic test script. |
| `backend/__pycache__/` | G | Compiled Python bytecode | **Delete** | Temporary generated cache files. |

---

### 2.3 Frontend Directory (`frontend/`)

| File / Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `frontend/src/App.js` | A | Top-level React state router and view coordinator | **Keep** in `frontend/src/` | Production frontend code. |
| `frontend/src/index.js` | A | React DOM mount entrypoint | **Keep** in `frontend/src/` | Production frontend code. |
| `frontend/src/index.css` | A | Design system tokens, styles, and hero background rules | **Keep** in `frontend/src/` | Production styling system. |
| `frontend/src/reportUtils.js` | A | Client-side jsPDF and autoTable PDF generator | **Keep** in `frontend/src/` | Production report generation utility. |
| `frontend/src/assets/crop-field-bg.png` | A | Homepage hero section agricultural background image | **Keep** in `frontend/src/assets/` | Required UI asset (1.08 MB). |
| `frontend/src/pages/HeroPage.js` | A | Homepage hero, metrics, how-it-works, and features view | **Keep** in `frontend/src/pages/` | Production page component. |
| `frontend/src/pages/OptionPage.js` | A | Input method selection page (Upload vs. Coordinates) | **Keep** in `frontend/src/pages/` | Production page component. |
| `frontend/src/pages/AnalysisPage.js` | A | Analysis workflow with live telemetry previews | **Keep** in `frontend/src/pages/` | Production page component. |
| `frontend/src/pages/ResultPage.js` | A | Prediction dashboard, OOD alerts, and agronomic insights | **Keep** in `frontend/src/pages/` | Production page component. |
| `frontend/src/pages/CropComparisonDashboard.js`| A | Multi-candidate crop comparison matrix | **Keep** in `frontend/src/pages/` | Production page component. |
| `frontend/src/pages/HistoryPage.js` | A | Interactive historical predictions explorer | **Keep** in `frontend/src/pages/` | Production page component. |
| `frontend/src/pages/HistoryPage.css` | A | Styles for history explorer component | **Keep** in `frontend/src/pages/` | Production styling component. |
| `frontend/public/index.html` | A | HTML5 template with Google Fonts preconnect | **Keep** in `frontend/public/` | Required for React web application. |
| `frontend/package.json` | A | Node.js manifest and dependency versions | **Keep** in `frontend/` | Required to build and run frontend. |
| `frontend/package-lock.json` | A | Exact dependency version lockfile | **Keep** in `frontend/` | Guarantees deterministic `npm install`. |
| `frontend/Dockerfile` | A | Multi-stage Docker containerization specification | **Keep** in `frontend/` | Containerization asset. |
| `frontend/.env` | A/Secret | React frontend API base URL configuration | **Protect** via `.gitignore` / create `.env.example` | Prevent accidental URL leak; provide sample. |
| `frontend/build/` | G | Production build artifacts | **Keep local / Ignore in git** | Build artifact; can be regenerated with `npm run build`. |
| `frontend/node_modules/` | G | Installed Node packages | **Ignore in git** (`.gitignore`) | Never commit `node_modules` to GitHub (huge size). |

---

### 2.4 Soil CNN Directory (`cnn/`)

| File / Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `cnn/predict_soil.py` | A | Production inference engine for soil classification | **Keep** in `cnn/` | Production CNN module; must remain in place. |
| `cnn/train_cnn.py` | B/C | MobileNetV2 fine-tuning pipeline | **Keep** in `cnn/` | Required for model training reproducibility. |
| `cnn/prepare_genuine_dataset.py`| B/C | Dataset augmentation and split generator | **Keep** in `cnn/` | Dataset preparation utility. |
| `cnn/generate_sample_images.py` | C | Diagnostic script generating synthetic soil samples | **Keep** in `cnn/` | Development testing tool. |
| `cnn/dataset/train/` | B | 200 genuine soil photographs (40 per class) | **Keep** in `cnn/dataset/train/` | Core training data needed to retrain or audit CNN. |
| `cnn/dataset/test/` | C | Genuine holdout test soil photographs | **Keep** in `cnn/dataset/test/` | Used by live evaluation tests and test scripts. |

---

### 2.5 Trained Models Directory (`models/`)

| File / Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `models/crop_model.pkl` | A | Production Random Forest Classifier (13.52 MB) | **Keep** in `models/` | **CRITICAL PRODUCTION ARTIFACT.** Active production engine. |
| `models/crop_model_xgboost_demo.pkl` | B/C | Academic Demonstration XGBoost Classifier (2.17 MB) | **Keep** in `models/` | Standalone comparison model for academic benchmarking. |
| `models/soil_cnn_model.keras` | A | Modern Keras MobileNetV2 soil classifier (13.98 MB) | **Keep** in `models/` | Preferred primary model format for TensorFlow 2.16+. |
| `models/soil_cnn_model.h5` | A | Legacy HDF5 MobileNetV2 model weights (13.76 MB) | **Keep** in `models/` | Multi-tier fallback format for legacy TensorFlow. |
| `models/soil_cnn_model.pkl` | A | Lightweight scikit-learn color centroid bundle (287 KB) | **Keep** in `models/` | Lightweight fallback for low-resource environments. |

---

### 2.6 Datasets & Data Directories (`datasets/` & `data/`)

| File / Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `datasets/Crop_recommendation_clean.csv` | B/C | Phase 5 clean dataset (1150 samples, 23 balanced classes) | **Keep** in `datasets/` | **CANONICAL TRAINING DATASET.** Used by both RF and XGBoost. |
| `datasets/Crop_recommendation.csv` | B/C | Original 2200-sample crop dataset | **Keep** in `datasets/` | Baseline comparative dataset; demonstrates legacy flaws. |
| `data/karnataka_main_places_npk_project_ready_v1.csv` | A/B | Published Karnataka district NPK soil fertility profiles | **Keep** in `data/` | **CANONICAL NPK REFERENCE.** Used by `npk_lookup.py`. |
| `data/predictions_history.json` | A | Runtime JSON persistence store for prediction history | **Keep** in `data/` | Preserves demonstration query history. |

---

### 2.7 Historical Backups (`BACKUP_*/`)

| Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `BACKUP_ORIGINAL/` | E | Pristine snapshot of legacy project before modernization | **Move** to `archive/backups/BACKUP_ORIGINAL/` | Preserves recovery point without cluttering root. |
| `BACKUP_PHASE9/` | E | Pre-Phase 9 codebase snapshot | **Move** to `archive/backups/BACKUP_PHASE9/` | Historical recovery point. |
| `BACKUP_PHASE10/` | E | Pre-Phase 10 codebase snapshot | **Move** to `archive/backups/BACKUP_PHASE10/` | Historical recovery point. |
| `BACKUP_FRONTEND_REDESIGN/` | E | Pre-redesign frontend snapshot | **Move** to `archive/backups/BACKUP_FRONTEND_REDESIGN/` | Historical recovery point for frontend UI. |
| `BACKUP_FRONTEND_FINAL_HERO/`| E | Pre-hero-image frontend snapshot | **Move** to `archive/backups/BACKUP_FRONTEND_FINAL_HERO/` | Historical recovery point for hero styling. |
| `BACKUP_XGBOOST_DEMO/` | E | Snapshot of production RF model and backend before XGBoost | **Move** to `archive/backups/BACKUP_XGBOOST_DEMO/` | Verifies production model integrity. |

---

### 2.8 Virtual Environments & Node Packages

| Folder | Category | Purpose | Recommendation | Rationale |
|:---|:---:|:---|:---:|:---|
| `.venv/` | G | Local Python virtual environment | **Keep local / Ignore in git** | Must NOT be pushed to GitHub (machine-specific binaries). |
| `frontend/node_modules/` | G | Local npm dependencies | **Keep local / Ignore in git** | Must NOT be pushed to GitHub (regenerated via `npm install`). |

---

## 3. Summary of Cleanup Strategy

1. **Root Organization:**
   - Consolidate all historical documentation into `docs/`.
   - Move chart/gallery images into `docs/assets/`.
   - Consolidate all historical backups under `archive/backups/`.
   - Consolidate test suites and diagnostic audits into `tests/`.
   - Move raw test result JSON files into `tests/results/`.
2. **Repository Root Essentials:**
   - `README.md` (comprehensive GitHub guide).
   - `requirements.txt` (root-level Python dependencies).
   - `.gitignore` (excludes `.venv`, `node_modules`, `.env`, caches).
   - `.env.example` (template for API keys).
   - `Dockerfile.backend` (containerization).
3. **Safety Guarantee:**
   - No production code modified.
   - No models or datasets deleted.
   - Standalone XGBoost academic comparison preserved.
   - Backward compatibility for all path lookups verified.
