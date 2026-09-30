# CropSense AI — System Run & Demonstration Manual

**Document Version:** 1.0  
**Phase:** 10 — Final Validation & Project Freeze  
**System:** CropSense AI (Precision Agricultural Advisory Platform)  
**Date:** September 2026  

---

## Prerequisites
- **Operating System:** Windows 10 / 11 (PowerShell terminal)
- **Python:** Python 3.10.x installed and available on PATH
- **Node.js:** Node.js 18+ and npm installed and available on PATH

---

## A. Environment Setup & Activation

The project includes a dedicated virtual environment in `.venv/`.

To activate in PowerShell:
```powershell
# Open terminal in project root directory:
cd c:\Users\shree\Downloads\major-project-demo1

# Activate virtual environment:
.\.venv\Scripts\Activate.ps1
```

If creating a new virtual environment from scratch:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## B. Dependency Installation

### 1. Backend Dependencies:
```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

### 2. Frontend Dependencies:
```powershell
cd frontend
npm install
cd ..
```

---

## C. Starting the Backend Server

The backend runs on FastAPI and Uvicorn on port `8000`.

From the project root:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Verification:** Open `http://localhost:8000/` in your browser. You should see:
```json
{"status": "ok", "message": "CropSense AI API is running. POST to /predict"}
```

---

## D. Starting the Frontend Server

Open a second PowerShell terminal in the project root:
```powershell
cd c:\Users\shree\Downloads\major-project-demo1\frontend
npm start
```

---

## E. Opening the Application

Once both servers are running:
1. Open Google Chrome or Microsoft Edge.
2. Navigate to: `http://localhost:3000`
3. You will be greeted by the CropSense AI dark green glassmorphic landing page.

---

## F. Performing a Live Demonstration Prediction

Follow this exact walkthrough during evaluation or viva:

1. On the landing page, click **"Analyze Soil"** or **"Get Started"**.
2. **Select Location:**
   - Click **"Detect Location"** for browser geolocation, OR
   - Manually enter standard Karnataka coordinates:
     - **Bengaluru:** Latitude: `12.9716`, Longitude: `77.5946`
     - **Kalaburagi:** Latitude: `17.3297`, Longitude: `76.8343`
     - **Dharwad:** Latitude: `15.4589`, Longitude: `75.0078`
3. **Upload Soil Photograph:**
   - Click the upload box or drag-and-drop a sample image from the test repository:
     - Red Soil sample: `cnn/dataset/test/red/test_red_000.jpg`
     - Black Soil sample: `cnn/dataset/test/black/test_black_000.jpg`
     - Loam Soil sample: `cnn/dataset/test/loamy/test_loamy_000.jpg`
     - Sand Soil sample: `cnn/dataset/test/sandy/test_sandy_000.jpg`
4. Click **"Begin Soil Analysis"**.
5. Observe the multi-stage visual execution:
   - **Soil Classification Banner:** Displays CNN predicted type (e.g., Red/Sandy/Black) and confidence percentage.
   - **NPK Data Badge:** Displays nearest district reference profile and provenance type (`published measured`).
   - **OOD Notice Banner:** Amber warning box highlights that inputs exceed empirical training limits and represent algorithmic tree extrapolation.
   - **Environmental Cards:** Displays live Temperature, Humidity, Rainfall, and pH (with fallback indicator if active).
   - **Recommended Crop Cards:** Displays top-3 ranked crops (e.g., Grapes, Muskmelon, Maize) with confidence %, market price, profit rating, season, and water need.
6. **Generate Report:**
   - Click **"Download PDF"** or **"Print Report"** to inspect the clean, printable summary containing the Soil Macronutrients table, NPK provenance, and OOD disclaimer.

---

## G. Running Automated Verification Suites

To verify system health programmatically:

```powershell
# Run the complete Phase 10 validation suite:
.\.venv\Scripts\python.exe backend/test_phase10_validation.py

# Run the 10-location Karnataka regression test:
.\.venv\Scripts\python.exe backend/test_phase9_full_regression.py
```
