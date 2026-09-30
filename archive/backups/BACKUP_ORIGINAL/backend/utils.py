"""utils.py — shared helpers for the backend."""
import os, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def root_path(*parts) -> str:
    """Return absolute path relative to the project root."""
    return os.path.join(ROOT_DIR, *parts)

def ensure_dirs():
    for d in ["models", "datasets"]:
        os.makedirs(root_path(d), exist_ok=True)

CROP_INFO: dict = {
    "rice":        {"profit": "High",     "yield": "3–5 tons/ha",    "price": "₹20–25/kg",  "season": "Monsoon", "water_need": "High"},
    "wheat":       {"profit": "High",     "yield": "2.5–4 tons/ha",  "price": "₹18–22/kg",  "season": "Winter",  "water_need": "Medium"},
    "maize":       {"profit": "Medium",   "yield": "4–6 tons/ha",    "price": "₹15–18/kg",  "season": "Kharif",  "water_need": "Medium"},
    "chickpea":    {"profit": "High",     "yield": "1–1.5 tons/ha",  "price": "₹50–60/kg",  "season": "Rabi",    "water_need": "Low"},
    "kidneybeans": {"profit": "High",     "yield": "1–2 tons/ha",    "price": "₹80–120/kg", "season": "Kharif",  "water_need": "Medium"},
    "pigeonpeas":  {"profit": "Medium",   "yield": "1–1.5 tons/ha",  "price": "₹55–70/kg",  "season": "Kharif",  "water_need": "Low"},
    "mothbeans":   {"profit": "Medium",   "yield": "0.5–1 ton/ha",   "price": "₹40–55/kg",  "season": "Kharif",  "water_need": "Low"},
    "mungbean":    {"profit": "Medium",   "yield": "0.8–1.2 tons/ha","price": "₹60–80/kg",  "season": "Zaid",    "water_need": "Low"},
    "blackgram":   {"profit": "Medium",   "yield": "0.8–1 ton/ha",   "price": "₹70–90/kg",  "season": "Kharif",  "water_need": "Low"},
    "lentil":      {"profit": "High",     "yield": "1–1.5 tons/ha",  "price": "₹60–80/kg",  "season": "Rabi",    "water_need": "Low"},
    "pomegranate": {"profit": "Very High","yield": "8–12 tons/ha",   "price": "₹40–80/kg",  "season": "Annual",  "water_need": "Low"},
    "banana":      {"profit": "High",     "yield": "20–30 tons/ha",  "price": "₹15–25/kg",  "season": "Annual",  "water_need": "High"},
    "mango":       {"profit": "Very High","yield": "5–8 tons/ha",    "price": "₹30–80/kg",  "season": "Summer",  "water_need": "Medium"},
    "grapes":      {"profit": "Very High","yield": "10–15 tons/ha",  "price": "₹40–100/kg", "season": "Annual",  "water_need": "Medium"},
    "watermelon":  {"profit": "High",     "yield": "20–30 tons/ha",  "price": "₹8–15/kg",   "season": "Summer",  "water_need": "High"},
    "muskmelon":   {"profit": "High",     "yield": "15–20 tons/ha",  "price": "₹10–18/kg",  "season": "Summer",  "water_need": "Medium"},
    "apple":       {"profit": "Very High","yield": "10–15 tons/ha",  "price": "₹60–150/kg", "season": "Winter",  "water_need": "Medium"},
    "orange":      {"profit": "High",     "yield": "10–15 tons/ha",  "price": "₹20–40/kg",  "season": "Winter",  "water_need": "Medium"},
    "papaya":      {"profit": "High",     "yield": "30–50 tons/ha",  "price": "₹10–20/kg",  "season": "Annual",  "water_need": "High"},
    "coconut":     {"profit": "High",     "yield": "80–100 nuts/palm","price": "₹15–30/nut", "season": "Annual",  "water_need": "High"},
    "cotton":      {"profit": "High",     "yield": "1.5–2.5 tons/ha","price": "₹55–65/kg",  "season": "Kharif",  "water_need": "Medium"},
    "jute":        {"profit": "Medium",   "yield": "2–3 tons/ha",    "price": "₹30–50/kg",  "season": "Kharif",  "water_need": "High"},
    "coffee":      {"profit": "Very High","yield": "1–2 tons/ha",    "price": "₹150–300/kg","season": "Annual",  "water_need": "Medium"},
    "pepper":      {"profit": "Very High","yield": "2–3 tons/ha",    "price": "₹250–400/kg","season": "Annual",  "water_need": "High"},
    "cardamom":    {"profit": "Very High","yield": "0.8–1.2 tons/ha","price": "₹1200–1600/kg","season": "Annual",  "water_need": "High"},
    "arecanut":    {"profit": "High",     "yield": "4–6 tons/ha",    "price": "₹20–30/kg",  "season": "Annual",  "water_need": "High"},
}

def crop_info(name: str) -> dict:
    return CROP_INFO.get(name.lower(), {
        "profit": "Medium", "yield": "N/A", "price": "N/A",
        "season": "N/A", "water_need": "Medium",
    })
