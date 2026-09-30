"""
history.py — Prediction history management
Stores and retrieves prediction history to/from JSON file
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(ROOT_DIR, "data")
HISTORY_FILE = os.path.join(HISTORY_DIR, "predictions_history.json")

os.makedirs(HISTORY_DIR, exist_ok=True)


def _load_history() -> List[Dict]:
    """Load prediction history from file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
        return []


def _save_history(history: List[Dict]) -> None:
    """Save prediction history to file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")


def save_prediction(
    location: str,
    latitude: float,
    longitude: float,
    soil_type: str,
    soil_confidence: float,
    temperature: float,
    humidity: float,
    rainfall: float,
    ph: float,
    organic_carbon: float,
    crops: List[Dict],
    image_name: str = "soil_image"
) -> Dict:
    """
    Save a prediction to history.
    Returns the saved prediction object with ID.
    """
    history = _load_history()

    # Generate unique ID (timestamp-based)
    prediction_id = datetime.now().isoformat()

    prediction = {
        "id": prediction_id,
        "timestamp": prediction_id,
        "location": location,
        "latitude": latitude,
        "longitude": longitude,
        "soil_type": soil_type,
        "soil_confidence": soil_confidence,
        "temperature": temperature,
        "humidity": humidity,
        "rainfall": rainfall,
        "ph": ph,
        "organic_carbon": organic_carbon,
        "crops": crops,
        "image_name": image_name,
    }

    history.insert(0, prediction)  # Add to front (latest first)
    _save_history(history)

    return prediction


def get_history(
    limit: int = 50,
    soil_type_filter: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict]:
    """
    Get prediction history with optional filtering.

    Args:
        limit: Max number of records to return
        soil_type_filter: Filter by soil type (case-insensitive)
        search: Search in location name
    """
    history = _load_history()

    # Apply filters
    if soil_type_filter:
        history = [p for p in history if p["soil_type"].lower() == soil_type_filter.lower()]

    if search:
        history = [p for p in history if search.lower() in p["location"].lower()]

    # Return limited results (already sorted by latest first)
    return history[:limit]


def get_prediction_by_id(prediction_id: str) -> Optional[Dict]:
    """Get a specific prediction by ID."""
    history = _load_history()
    for prediction in history:
        if prediction["id"] == prediction_id:
            return prediction
    return None


def delete_prediction(prediction_id: str) -> bool:
    """Delete a prediction by ID."""
    history = _load_history()
    original_len = len(history)
    history = [p for p in history if p["id"] != prediction_id]

    if len(history) < original_len:
        _save_history(history)
        return True
    return False


def get_soil_types() -> List[str]:
    """Get unique soil types from history."""
    history = _load_history()
    soil_types = sorted(set(p["soil_type"] for p in history))
    return soil_types


def get_stats() -> Dict:
    """Get prediction statistics."""
    history = _load_history()

    if not history:
        return {
            "total_predictions": 0,
            "unique_locations": 0,
            "unique_soil_types": 0,
            "avg_soil_confidence": 0.0,
        }

    soil_types = set(p["soil_type"] for p in history)
    locations = set(p["location"] for p in history)
    avg_conf = sum(p["soil_confidence"] for p in history) / len(history)

    return {
        "total_predictions": len(history),
        "unique_locations": len(locations),
        "unique_soil_types": len(soil_types),
        "avg_soil_confidence": round(avg_conf, 3),
    }