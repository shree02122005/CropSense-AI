# 🌾 CropSense AI — Full-Stack Crop Recommendation System

> Hybrid CNN + Random Forest AI | FastAPI Backend | React Frontend
> Fully runnable in VS Code without any manual fixes.

---

## 📁 Project Structure

```
crop-app/
├── backend/
│   ├── main.py              ← FastAPI server
│   ├── predict_api.py       ← Hybrid AI pipeline
│   ├── train_model.py       ← Train RandomForest
│   ├── requirements.txt     ← Python dependencies
│   └── utils.py             ← Shared helpers & crop info
│
├── cnn/
│   ├── train_cnn.py              ← Train soil classifier
│   ├── predict_soil.py           ← Load & run soil model
│   ├── generate_sample_images.py ← Generate synthetic soil images
│   └── dataset/train/
│       ├── black/  clay/  loamy/  red/  sandy/
│
├── datasets/
│   └── Crop_recommendation.csv   ← 1150-row training dataset (pre-generated)
│
├── models/
│   ├── crop_model.pkl            ← Trained RandomForest (pre-trained)
│   └── soil_cnn_model.pkl        ← Trained soil classifier (pre-trained)
│
├── frontend/
│   ├── package.json
│   ├── public/index.html
│   └── src/
│       ├── App.js
│       ├── index.js / index.css
│       └── pages/
│           ├── HeroPage.js
│           ├── OptionPage.js
│           ├── AnalysisPage.js
│           └── ResultPage.js
│
└── README.md
```

---

## ✅ Pre-built Models Included

The zip already contains:
- `models/crop_model.pkl`      — RandomForest trained at 91% accuracy
- `models/soil_cnn_model.pkl`  — Soil classifier trained at 100% accuracy
- `datasets/Crop_recommendation.csv` — 1150-row dataset
- `cnn/dataset/train/*/` — 150 synthetic soil images (30 per class)

**You can skip Steps 2–4 below and jump straight to running the app.**

---

## 🚀 Quick Start (VS Code)

### Step 1 — Install Python backend dependencies

Open a terminal in the project root:

```bash
cd backend
python -m venv venv

# Activate virtual environment:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> **Note on TensorFlow:** `requirements.txt` includes TensorFlow for CNN training.
> If TensorFlow fails to install on your platform, remove it from requirements.txt —
> the app works with the pre-built sklearn soil model (`soil_cnn_model.pkl`).

---

### Step 2 — (Optional) Regenerate synthetic soil images

Only needed if `cnn/dataset/train/` is empty.

```bash
# From project root
python cnn/generate_sample_images.py
```

Generates 30 JPG images per soil class (150 total).

---

### Step 3 — (Optional) Re-train the soil classifier

```bash
# From project root
python cnn/train_cnn.py
```

- With TensorFlow installed → saves `models/soil_cnn_model.h5`
- Without TensorFlow → saves `models/soil_cnn_model.pkl` (sklearn, 100% accuracy)

---

### Step 4 — (Optional) Re-train the crop ML model

```bash
# From project root
python backend/train_model.py
```

Trains RandomForestClassifier on `datasets/Crop_recommendation.csv`.
Prints accuracy (~91%) and saves `models/crop_model.pkl`.

---

### Step 5 — Start the FastAPI backend

```bash
# From project root (with venv activated)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/

---

### Step 6 — Start the React frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm start
```

Opens at: **http://localhost:3000**

---

## 🌐 Using the App

1. Click **Start Analysis**
2. Select **Auto Location** (or Manual)
3. Click **Detect My Location** → allow browser GPS access
4. Upload a soil photo (or any JPG/PNG for testing)
5. Click **Run Hybrid AI Analysis**
6. View results: soil type, weather, and top crop recommendations

---

## 🔑 OpenWeather API Key (Optional)

The app works **without** a real API key — it uses fallback weather values based on your latitude. For live weather:

1. Get a free key at https://openweathermap.org/api
2. Edit `backend/predict_api.py` line 18:
   ```python
   OPENWEATHER_API_KEY = "your_real_key_here"
   ```

---

## 🧠 System Architecture

```
[Browser]
    │
    ├─ GPS → lat, lon
    ├─ Soil image upload
    │
    ▼
[FastAPI /predict]
    │
    ├─ 1. Soil Classifier  (CNN/RF) → soil type + confidence
    ├─ 2. OpenWeather API           → temp, humidity, rainfall
    ├─ 3. SoilGrids API             → pH, organic carbon
    ├─ 4. Fixed: N=90, P=40, K=40
    │
    ├─ Feature vector: [N, P, K, temp, humidity, pH, rainfall]
    │
    └─ 5. RandomForestClassifier → top-3 crop predictions
    │
    ▼
[React Result Dashboard]
    ├─ Soil type + confidence
    ├─ Weather metrics
    ├─ Crop cards with confidence bars, yield, price, season
```

---

## 📦 Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | React 18, Framer Motion, Axios, Lucide  |
| Backend   | FastAPI, Uvicorn, Python 3.10+          |
| ML        | scikit-learn RandomForestClassifier     |
| CNN       | TensorFlow/Keras (sklearn fallback)     |
| Weather   | OpenWeatherMap API (fallback included)  |
| Soil      | SoilGrids REST API (fallback included)  |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Activate venv: `source venv/bin/activate` |
| `CORS error` in browser | Backend must be running on port 8000 |
| `Location denied` | Allow location in browser settings |
| `soil_cnn_model not found` | Run `python cnn/train_cnn.py` |
| `crop_model not found` | Run `python backend/train_model.py` |
| TensorFlow won't install | Remove from requirements.txt — sklearn model works fine |

---

## 📝 API Reference

### `POST /predict`

**Form fields:**

| Field     | Type   | Description          |
|-----------|--------|----------------------|
| image     | file   | Soil photo (JPG/PNG) |
| latitude  | float  | GPS latitude         |
| longitude | float  | GPS longitude        |

**Response:**

```json
{
  "location": "Bengaluru",
  "soil_type": "Loamy",
  "soil_confidence": 0.95,
  "temperature": 27.5,
  "humidity": 68.0,
  "rainfall": 85.0,
  "ph": 6.5,
  "organic_carbon": 1.5,
  "N": 90,
  "P": 40,
  "K": 40,
  "crops": [
    {
      "name": "Rice",
      "confidence": 0.76,
      "profit": "High",
      "yield": "3-5 tons/ha",
      "price": "Rs.20-25/kg",
      "season": "Monsoon",
      "water_need": "High"
    }
  ]
}
```
