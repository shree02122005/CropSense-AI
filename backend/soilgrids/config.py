"""Configuration for the ISRIC SoilGrids v2.0 REST client."""
import os

BASE_URL = os.getenv("SOILGRIDS_BASE_URL", "https://rest.isric.org/soilgrids/v2.0")
QUERY_PATH = "/properties/query"

# Properties requested for the chatbot (SoilGrids layer names).
PROPERTIES = ["phh2o", "clay", "sand", "silt", "nitrogen", "soc", "cec", "bdod", "cfvo"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm"]          # root zone of most field crops
VALUES = ["mean", "Q0.05", "Q0.5", "Q0.95", "uncertainty"]

# The full 9-property query regularly times out on the (beta) service, so we
# fetch in small batches. Batches that still fail are split into single properties.
BATCH_SIZE = int(os.getenv("SOILGRIDS_BATCH_SIZE", "3"))

REQUEST_TIMEOUT_S = float(os.getenv("SOILGRIDS_TIMEOUT_S", "25"))
MAX_RETRIES = int(os.getenv("SOILGRIDS_MAX_RETRIES", "2"))        # retries after the first try
BACKOFF_BASE_S = float(os.getenv("SOILGRIDS_BACKOFF_S", "1.5"))   # 1.5s, 3s, 6s ... (+ jitter)
TOTAL_BUDGET_S = float(os.getenv("SOILGRIDS_TOTAL_BUDGET_S", "60"))  # whole profile fetch

# ISRIC fair-use policy for the REST API: at most ~5 requests per minute.
RATE_LIMIT_CALLS = int(os.getenv("SOILGRIDS_RATE_LIMIT_CALLS", "5"))
RATE_LIMIT_PERIOD_S = 60.0

CACHE_PATH = os.getenv(
    "SOILGRIDS_CACHE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "soilgrids_cache.json"),
)
CACHE_TTL_S = 30 * 24 * 3600          # soil properties are static model predictions
PARTIAL_CACHE_TTL_S = 3600            # retry missing properties after an hour
COORD_PRECISION = 3                   # ~100 m; SoilGrids resolution is 250 m

SOURCE_NAME = "ISRIC SoilGrids 2.0 (REST API v2.0, global 250 m predictions)"

PROPERTY_INFO = {
    "phh2o":    {"label": "Soil pH (in water)", "unit": "pH"},
    "clay":     {"label": "Clay content", "unit": "%"},
    "sand":     {"label": "Sand content", "unit": "%"},
    "silt":     {"label": "Silt content", "unit": "%"},
    "nitrogen": {"label": "Total nitrogen", "unit": "g/kg"},
    "soc":      {"label": "Soil organic carbon", "unit": "g/kg"},
    "cec":      {"label": "Cation exchange capacity (pH 7)", "unit": "cmol(c)/kg"},
    "bdod":     {"label": "Bulk density (fine earth)", "unit": "kg/dm³"},
    "cfvo":     {"label": "Coarse fragments (gravel/stones)", "unit": "vol %"},
}

# Parameters farmers often ask about that SoilGrids does NOT provide.
NOT_PROVIDED = [
    "Available phosphorus (P)",
    "Available potassium (K)",
    "Plant-available nitrogen / NPK fertiliser status (SoilGrids gives TOTAL nitrogen only)",
    "Real-time soil moisture",
    "Micronutrients (zinc, iron, boron, etc.)",
    "Electrical conductivity / salinity and sodicity (ESP)",
    "Field-specific measurements (SoilGrids values are modelled estimates for a 250 m area)",
]
