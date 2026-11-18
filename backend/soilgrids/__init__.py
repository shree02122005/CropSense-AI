"""ISRIC SoilGrids v2.0 integration (independent of the chatbot / RAG code)."""
from .client import SoilGridsUnavailable
from .service import get_soil_profile, soil_summary_for_ui

__all__ = ["get_soil_profile", "soil_summary_for_ui", "SoilGridsUnavailable"]
