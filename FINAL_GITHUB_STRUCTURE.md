# CropSense AI — Final GitHub Repository Structure

This document presents the complete and finalized directory tree of the CropSense AI repository prepared for GitHub.

---

```
CropSense-AI/
├── README.md                           # Main GitHub repository landing page & architectural guide
├── requirements.txt                    # Project-level Python dependencies specification
├── .gitignore                          # Git exclusion rules (venv, node_modules, secrets, caches)
├── .env.example                        # Template environment variables for API keys
├── Dockerfile.backend                  # Containerization file for backend deployment
│
├── backend/                            # FastAPI Application & ML Pipelines
│   ├── main.py                         # FastAPI server routes, middleware & history endpoints
│   ├── predict_api.py                  # Core prediction engine & telemetry orchestrator
│   ├── history.py                      # Local query persistence & statistics engine
│   ├── npk_lookup.py                   # Geographic nearest-neighbor Karnataka NPK lookup
│   ├── utils.py                        # Agronomic crop metadata, market prices & path helpers
│   ├── requirements.txt                # Backend Python dependencies
│   ├── train_model.py                  # Legacy Random Forest training reference
│   ├── retrain_and_evaluate.py         # Production Random Forest baseline training script
│   ├── train_xgboost_demo.py           # Academic demonstration XGBoost training script
│   ├── compare_models.py               # Empirical model comparison runner (RF vs. XGBoost)
│   ├── create_clean_dataset.py         # Phase 5 dataset cleaning & red-soil balancing script
│   ├── inspect_dataset.py              # Dataset schema & class distribution inspector
│   ├── model_comparison_results.json   # Machine-readable output of RF vs. XGBoost benchmark
│   ├── xgboost_demo_metrics.json       # Machine-readable output of XGBoost evaluation
│   └── data/
│       └── karnataka_main_places_npk_project_ready_v1.csv  # Local fallback NPK reference
│
├── frontend/                           # React 18 Web Application
│   ├── package.json                    # Node dependencies & npm scripts
│   ├── package-lock.json               # Deterministic dependency lockfile
│   ├── Dockerfile                      # Containerization file for frontend deployment
│   ├── .env.example                    # Template environment variables for frontend API URL
│   ├── public/
│   │   └── index.html                  # HTML5 base document with font preconnects
│   └── src/
│       ├── App.js                      # View router & application state coordinator
│       ├── index.js                    # React DOM entrypoint
│       ├── index.css                   # Global styles, dark forest-green palette & responsive hero
│       ├── reportUtils.js              # Production jsPDF & autoTable agronomic PDF generator
│       ├── assets/
│       │   └── crop-field-bg.png       # High-resolution agricultural hero background photograph
│       └── pages/
│           ├── HeroPage.js             # Homepage hero, holdout metrics, how-it-works & CTA
│           ├── OptionPage.js           # Soil photo upload vs. GPS coordinate selector
│           ├── AnalysisPage.js         # Interactive analysis view with live telemetry preview
│           ├── ResultPage.js           # Prediction results, OOD alerts, economics & insights
│           ├── CropComparisonDashboard.js # Multi-crop comparative evaluation matrix
│           ├── HistoryPage.js          # Interactive historical predictions explorer
│           └── HistoryPage.css         # Styles for history component
│
├── cnn/                                # Soil Classification Deep Neural Network
│   ├── predict_soil.py                 # MobileNetV2 inference engine, blur/lighting domain checks
│   ├── train_cnn.py                    # MobileNetV2 transfer-learning training script
│   ├── prepare_genuine_dataset.py      # Dataset augmentation & class balancing utility
│   ├── generate_sample_images.py       # Synthetic soil image generation tool
│   └── dataset/
│       ├── train/                      # 200 authentic soil training photographs (5 classes)
│       │   ├── black/
│       │   ├── clay/
│       │   ├── loamy/
│       │   ├── red/
│       │   └── sandy/
│       └── test/                       # Genuine holdout evaluation test photographs
│           ├── black/
│           ├── clay/
│           ├── loamy/
│           ├── red/
│           └── sandy/
│
├── datasets/                           # Tabular Crop Recommendation Datasets
│   ├── Crop_recommendation_clean.csv   # Canonical Phase 5 training dataset (1150 samples, 23 crops)
│   └── Crop_recommendation.csv         # Baseline legacy 2200-sample dataset
│
├── data/                               # Spatial Reference Maps & Runtime Stores
│   ├── karnataka_main_places_npk_project_ready_v1.csv  # Canonical Karnataka district NPK survey
│   └── predictions_history.json        # Runtime persistent JSON store for user queries
│
├── models/                             # Serialized Machine Learning Model Artifacts
│   ├── crop_model.pkl                  # Production Random Forest Model (13.52 MB, 93.04% acc)
│   ├── crop_model_xgboost_demo.pkl     # Academic Demo XGBoost Model (2.17 MB, 90.87% acc)
│   ├── soil_cnn_model.keras            # Production MobileNetV2 CNN (13.98 MB, Keras format)
│   ├── soil_cnn_model.h5               # Multi-tier HDF5 fallback weights (13.76 MB)
│   └── soil_cnn_model.pkl              # Lightweight color centroid fallback (287 KB)
│
├── docs/                               # Consolidated Technical & Academic Documentation
│   ├── MODEL_FILES.md                  # Comprehensive model specifications & operational roles
│   ├── DATASET_FILES.md                # Dataset provenance, cleaning methodology & schemas
│   ├── RUN_INSTRUCTIONS.md             # Developer setup, virtualenv & execution guide
│   ├── MODEL_BASELINE_RESULTS.md       # Phase 6 Random Forest baseline training & holdout metrics
│   ├── XGBOOST_DEMO_COMPARISON.md      # Side-by-side RF vs. XGBoost technical benchmark
│   ├── XGBOOST_DEMO_README.md          # Step-by-step XGBoost reproduction commands
│   ├── LOCATION_TEST_RESULTS.md        # 10-location empirical Karnataka field testing report
│   ├── NPK_INFERENCE_COMPATIBILITY.md  # Scientific analysis of NPK distribution shifts & OOD bounds
│   ├── VIVA_DEMO_NOTES.md              # Complete viva examination defense cheat sheet
│   ├── FINAL_PROJECT_STATUS.md         # Comprehensive engineering achievements & architecture
│   ├── FINAL_HERO_BACKGROUND_UPDATE.md # Documentation of local hero background integration
│   ├── FRONTEND_REDESIGN_REPORT.md     # UI/UX design system & responsive layout report
│   ├── OPENWEATHER_AUDIT_REPORT.md     # Weather API integration & resilience audit
│   ├── OPENWEATHER_FIX_SUMMARY.md      # Weather fallback implementation summary
│   ├── OPENWEATHER_TECHNICAL_REFERENCE.md # Weather data structures & schemas
│   ├── PHASE9_FINAL_INTEGRATION_REPORT.md # System integration & stability test report
│   ├── PHASE10_FINAL_REPORT.md         # Phase 10 demo readiness & code audit report
│   ├── PHASE10_PROJECT_STRUCTURE.md    # Architectural directory map & component responsibilities
│   ├── PROJECT_CLEANUP_INVENTORY.md    # Complete pre-cleanup categorization audit
│   ├── SOIL_CLASSIFICATION_IMPROVEMENTS.md # Deep learning classifier enhancements
│   └── assets/                         # Visual assets & benchmark charts
│       ├── soil_color_palette.png      # Soil color centroid visualization
│       ├── soil_texture_ranges.png     # Laplacian texture range analysis
│       ├── soil_training_gallery.png   # Genuine soil photograph gallery (3.6 MB)
│       └── XGBOOST_RF_COMPARISON.png   # Benchmark chart: Random Forest vs. XGBoost
│
├── tests/                              # Automated Test Suites & Verification Scripts
│   ├── test_final_health.py            # Quick end-to-end live health verification script
│   ├── test_phase10_validation.py      # Comprehensive 5-domain demo readiness test suite
│   ├── test_phase9_full_regression.py  # 10-location regression test against baseline
│   ├── test_phase9_comprehensive.py    # 10-domain stability & integration test suite
│   ├── test_phase8_locations.py        # End-to-end Karnataka location test suite
│   ├── test_phase7_locations.py        # Phase 7 location test runner
│   ├── test_prediction_flow.py         # Basic smoke test of prediction flow
│   ├── audit_fetch_weather.py          # Weather API diagnostic test script
│   ├── audit_predictions.py            # Historical prediction diagnostic test script
│   ├── audit_soilgrids.py              # SoilGrids API diagnostic test script
│   ├── audit_soil_classifier.py        # Soil classifier heuristic test script
│   ├── test_report_fixes.js            # Node report generation test script
│   ├── reportUtils.js                  # CommonJS report stub for test_report_fixes.js
│   └── results/                        # Machine-readable test execution logs
│       ├── phase10_validation_results.json    # Phase 10 validation audit summary
│       ├── phase9_regression_comparison.json  # Phase 9 regression comparison log
│       ├── phase8_karnataka_test_results.json  # Phase 8 Karnataka location baseline
│       └── phase7_backend_test_results.json   # Phase 7 test results
│
└── archive/                            # Consolidated Historical Backups & Recovery Points
    └── backups/
        ├── BACKUP_ORIGINAL/            # Pristine original prototype snapshot
        ├── BACKUP_PHASE9/              # Pre-Phase 9 codebase recovery snapshot
        ├── BACKUP_PHASE10/             # Pre-Phase 10 codebase recovery snapshot
        ├── BACKUP_FRONTEND_REDESIGN/   # Pre-redesign frontend snapshot
        ├── BACKUP_FRONTEND_FINAL_HERO/ # Pre-final-hero frontend snapshot
        └── BACKUP_XGBOOST_DEMO/        # Snapshot verifying RF model before XGBoost
```
