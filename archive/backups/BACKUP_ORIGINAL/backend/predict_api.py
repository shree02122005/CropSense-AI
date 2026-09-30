"""
predict_api.py
──────────────
Core prediction pipeline:
  1. Soil CNN  → soil type
  2. OpenWeather API → weather (with fallback)
  3. SoilGrids API   → pH, organic carbon (with fallback)
  4. RandomForest    → top-3 crop predictions
"""
import os, sys, asyncio
from dotenv import load_dotenv
import numpy as np
import joblib

# ── Adjust path so cnn/ module is importable ─────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from cnn.predict_soil import predict_soil_from_bytes, SOIL_CONFIDENCE_THRESHOLD, InvalidSoilImage, SoilProcessingError
from backend.utils import root_path, crop_info

import httpx

# ── OpenWeather API key — use environment variable for live data ──────────────
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_KEY")

# ── Model paths ───────────────────────────────────────────────────────────────
ML_MODEL_PATH = root_path("models", "crop_model.pkl")

SOIL_TYPE_LABELS = {
    "black": 0,
    "clay": 1,
    "loamy": 2,
    "red": 3,
    "sandy": 4,
}

_ml_model = None

def _load_ml_model():
    global _ml_model
    if _ml_model is None:
        _ml_model = joblib.load(ML_MODEL_PATH)
    return _ml_model


def _verify_ml_model_features(model):
    # Ensure model expects 8 features as used during training
    if not hasattr(model, "n_features_in_"):
        raise RuntimeError("Loaded ML model missing 'n_features_in_' attribute")
    if model.n_features_in_ != 8:
        raise RuntimeError(f"Loaded ML model expects {model.n_features_in_} features, but pipeline uses 8 features")


def _soil_type_to_encoded(soil_type: str) -> int:
    if not soil_type:
        raise ValueError("No soil type available for crop prediction")
    normalized = str(soil_type).strip().lower()
    encoded = SOIL_TYPE_LABELS.get(normalized)
    if encoded is None:
        print(f"Warning: soil_type '{soil_type}' not recognized; defaulting to loamy")
        encoded = SOIL_TYPE_LABELS["loamy"]
    return encoded


# ── Weather ───────────────────────────────────────────────────────────────────
async def _fetch_weather(lat: float, lon: float):
    try:
        import traceback
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        print(f"[_fetch_weather] OPENWEATHER_API_KEY prefix: {OPENWEATHER_API_KEY[:8] if OPENWEATHER_API_KEY else '<missing>'}")
        print(f"[_fetch_weather] Generated URL: {url}")
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
        print(f"[_fetch_weather] HTTP Status Code: {r.status_code}")
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")
        d = r.json()
        print(f"[_fetch_weather] JSON Response: {d}")
        temp = float(d["main"]["temp"])
        humidity = float(d["main"]["humidity"])
        rainfall = float(d.get("rain", {}).get("1h", 0) or d.get("rain", {}).get("3h", 0) or 0)
        location = d.get("name", "Unknown")
        print(f"[_fetch_weather] Extracted Values:")
        print(f"  - Temperature: {temp}°C")
        print(f"  - Humidity: {humidity}%")
        print(f"  - Rainfall: {rainfall}mm")
        print(f"  - Location: {location}")
        print(f"[_fetch_weather] ✓ API SUCCESS - Returning live data")
        return temp, humidity, rainfall, location
    except Exception as e:
        print(f"[_fetch_weather] ❌ EXCEPTION CAUGHT: {type(e).__name__}: {e}")
        traceback.print_exc()
        print("USING WEATHER FALLBACK")
        return _weather_fallback(lat, lon)


def _weather_fallback(lat: float, lon: float):
    print(f"[_weather_fallback] Called for lat={lat}, lon={lon}")
    print("USING WEATHER FALLBACK")
    if abs(lat) <= 23:
        temp = 28.0 if lat >= 0 else 24.0
        humidity = 75.0
        rainfall = 110.0
    elif abs(lat) <= 35:
        temp = 24.0
        humidity = 65.0
        rainfall = 70.0
    elif abs(lat) <= 50:
        temp = 18.0
        humidity = 60.0
        rainfall = 40.0
    else:
        temp = 10.0
        humidity = 55.0
        rainfall = 20.0
    print(f"[_weather_fallback] Returning fallback values: temp={temp}°C, humidity={humidity}%, rainfall={rainfall}mm")
    return temp, humidity, rainfall, f"Fallback location ({lat:.2f}, {lon:.2f})"


# ── Soil value normalization helpers ──────────────────────────────────────────
def _normalize_ph(raw_ph):
    try:
        value = float(raw_ph)
    except (TypeError, ValueError):
        return None

    if 3.5 <= value <= 9.0:
        return value

    for divisor in (10.0, 100.0, 1000.0):
        candidate = value / divisor
        if 3.5 <= candidate <= 9.0:
            return candidate

    return None


def _normalize_soc(raw_soc):
    try:
        value = float(raw_soc)
    except (TypeError, ValueError):
        return None

    if 0 <= value <= 10:
        return value

    for divisor in (10.0, 100.0, 1000.0):
        candidate = value / divisor
        if 0 <= candidate <= 10.0:
            return round(candidate, 2)

    return None


# ── SoilGrids ─────────────────────────────────────────────────────────────────
async def _fetch_soil(lat: float, lon: float):
    try:
        url = (
            "https://rest.isric.org/soilgrids/v2.0/properties/query"
            f"?lon={lon}&lat={lat}&property=phh2o&property=soc&depth=0-5cm&value=mean"
        )
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(url)
        if r.status_code != 200:
            raise ValueError(f"HTTP {r.status_code}")
        d = r.json()

        layers = {}
        for layer in d.get("properties", {}).get("layers", []):
            name = layer.get("name")
            if not name:
                continue

            mean_value = None
            for depth in layer.get("depths", []):
                if depth.get("label") == "0-5cm" or (
                    isinstance(depth.get("range"), dict)
                    and depth["range"].get("top_depth") == 0
                    and depth["range"].get("bottom_depth") == 5
                ):
                    mean_value = depth.get("values", {}).get("mean")
                    if mean_value is not None:
                        break

            if mean_value is None and layer.get("depths"):
                mean_value = layer["depths"][0].get("values", {}).get("mean")

            layers[name] = mean_value

        raw_ph = layers.get("phh2o")
        raw_soc = layers.get("soc")

        ph_value = _normalize_ph(raw_ph)
        soc_value = _normalize_soc(raw_soc)

        if ph_value is None or not (3.5 <= ph_value <= 9.0):
            ph_value = None
        if soc_value is None or not (0 <= soc_value <= 10.0):
            soc_value = None

        if ph_value is None or soc_value is None:
            return _soil_fallback(lat, lon)

        return round(ph_value, 2), round(soc_value, 2)
    except Exception:
        return _soil_fallback(lat, lon)


def _soil_fallback(lat: float, lon: float):
    if abs(lat) <= 23:
        return 5.8, 2.5
    if abs(lat) <= 35:
        return 6.2, 2.0
    return 6.6, 1.5


# ── Region-aware crop weighting ───────────────────────────────────────────────
def _tropical_weighting(lat: float, lon: float, humidity: float, temperature: float):
    weights = {
        "coffee": 1.0,
        "banana": 1.0,
        "pepper": 1.0,
        "cardamom": 1.0,
        "arecanut": 1.0,
    }

    # Humid tropical zones get a gentle boost for tropical plantation crops
    if abs(lat) <= 23 and humidity >= 60 and temperature >= 18:
        weights.update({
            "coffee": 1.25,
            "banana": 1.15,
            "pepper": 1.25,
            "cardamom": 1.25,
            "arecanut": 1.20,
        })

    # Specific bias for the Coorg/Kodagu region
    if 11.0 <= lat <= 13.0 and 74.0 <= lon <= 77.0:
        weights.update({
            "coffee": 1.45,
            "banana": 1.20,
            "pepper": 1.40,
            "cardamom": 1.40,
            "arecanut": 1.30,
        })

    return weights


# ── ML prediction ─────────────────────────────────────────────────────────────
def _predict_crops(N, P, K, temp, humidity, ph, rainfall, soil_type_encoded, latitude, longitude):
    model = _load_ml_model()
    _verify_ml_model_features(model)
    # Always use the 8-feature vector matching training order
    feat = np.array([[N, P, K, temp, humidity, ph, rainfall, soil_type_encoded]])
    print("ML feature vector:", feat.tolist())

    proba = model.predict_proba(feat)[0]

    weights = _tropical_weighting(latitude, longitude, humidity, temp)
    adjusted = np.copy(proba)
    for idx, crop in enumerate(model.classes_):
        adjusted[idx] *= weights.get(str(crop).lower(), 1.0)

    total = float(np.sum(adjusted))
    if total > 0:
        adjusted = adjusted / total

    top3 = np.argsort(adjusted)[::-1][:3]
    return [(model.classes_[i], float(adjusted[i])) for i in top3]


# ── Soil image validation ──────────────────────────────────────────────────────
def _validate_soil_image(soil_type: str, soil_conf: float, min_confidence: float = SOIL_CONFIDENCE_THRESHOLD) -> bool:
    """Validate if uploaded image is actually a soil image based on CNN confidence"""
    if soil_conf < min_confidence:
        return False
    # Check if soil_type is valid (not 'unknown' or empty)
    if not soil_type or soil_type.lower() == 'unknown':
        return False
    return True


# ── Main predict function ─────────────────────────────────────────────────────
async def predict_crop(image_bytes: bytes, latitude: float, longitude: float) -> dict:
    # Step 1: soil type
    soil_type, soil_conf = predict_soil_from_bytes(image_bytes)
    
    # Validate soil image before proceeding
    if not _validate_soil_image(soil_type, soil_conf):
        raise ValueError(f"Please upload a valid soil image. Detected: {soil_type} (confidence: {soil_conf:.1%})")

    # Step 2 & 3: weather + soil data (run concurrently)
    (temp, humidity, rainfall, location), (ph, organic_carbon) = await asyncio.gather(
        _fetch_weather(latitude, longitude),
        _fetch_soil(latitude, longitude),
    )

    # Step 4: ML prediction (N,P,K fixed as specified)
    N, P, K = 90, 40, 40
    soil_type_encoded = _soil_type_to_encoded(soil_type)
    print(f"Predicted soil type: {soil_type} | Encoded soil_type: {soil_type_encoded}")

    top_crops = _predict_crops(
        N, P, K, temp, humidity, ph, rainfall,
        soil_type_encoded, latitude, longitude
    )

    crops = []
    for name, confidence in top_crops:
        info = crop_info(name)
        crops.append({
            "name":       name.title(),
            "confidence": round(confidence, 3),
            **info,
        })

    return {
        "location":            location,
        "soil_type":           soil_type.title(),
        "soil_type_encoded":   soil_type_encoded,
        "soil_confidence":     round(soil_conf, 3),
        "temperature":         round(temp, 1),
        "humidity":            round(humidity, 1),
        "rainfall":            round(rainfall, 1),
        "ph":                  round(ph, 2),
        "organic_carbon":      round(organic_carbon, 2),
        "N":                   N,
        "P":                   P,
        "K":                   K,
        "feature_vector":      [N, P, K, round(temp, 1), round(humidity, 1), round(ph, 2), round(rainfall, 1), soil_type_encoded],
        "crops":               crops,
    }
