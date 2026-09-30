from pathlib import Path
import math
import pandas as pd


def _find_data_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "karnataka_main_places_npk_project_ready_v1.csv",
        Path(__file__).resolve().parent / "data" / "karnataka_main_places_npk_project_ready_v1.csv",
        Path.cwd() / "data" / "karnataka_main_places_npk_project_ready_v1.csv",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]

DATA_PATH = _find_data_path()



def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


def get_nearest_npk(latitude, longitude):

    df = pd.read_csv(DATA_PATH)

    df = df.dropna(
        subset=[
            "latitude",
            "longitude",
            "N_model_input",
            "P_model_input",
            "K_model_input",
        ]
    )

    best_row = None
    best_distance = float("inf")

    for _, row in df.iterrows():

        distance = _haversine_km(
            latitude,
            longitude,
            float(row["latitude"]),
            float(row["longitude"]),
        )

        if distance < best_distance:
            best_distance = distance
            best_row = row

    if best_row is None:
        raise ValueError("No NPK reference location found.")

    return {
        "N": float(best_row["N_model_input"]),
        "P": float(best_row["P_model_input"]),
        "K": float(best_row["K_model_input"]),
        "district": str(best_row["district"]),
        "reference_place": str(best_row["reference_place"]),
        "distance_km": round(best_distance, 2),
        "source_type": str(best_row["source_type"]),
        "source_note": str(best_row["source_note"]),
    }
