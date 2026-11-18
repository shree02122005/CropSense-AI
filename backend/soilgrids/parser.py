"""
Validate and normalise SoilGrids /properties/query responses.

SoilGrids stores values as integers in "mapped units" (e.g. pH*10, g/kg, cg/cm³).
Each layer carries `unit_measure.d_factor`; dividing by it gives "target units"
(pH, %, kg/dm³ …). We convert with the factor the API returns, keep the original
units, and keep the 5 %/95 % prediction quantiles and the uncertainty index.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import config
from .interpret import organic_carbon_class, ph_class, screening_flags, usda_texture_class


class InvalidSoilGridsResponse(ValueError):
    """The response does not look like a SoilGrids properties document."""


DEPTH_THICKNESS = {"0-5cm": 5, "5-15cm": 10, "15-30cm": 15}


def validate_response(payload: Any) -> List[dict]:
    """Return the list of layers, or raise InvalidSoilGridsResponse."""
    if not isinstance(payload, dict):
        raise InvalidSoilGridsResponse("response is not a JSON object")
    layers = (payload.get("properties") or {}).get("layers")
    if not isinstance(layers, list):
        raise InvalidSoilGridsResponse("missing properties.layers")
    for layer in layers:
        if not isinstance(layer, dict) or "name" not in layer or not isinstance(layer.get("depths"), list):
            raise InvalidSoilGridsResponse("malformed layer")
        um = layer.get("unit_measure") or {}
        if not isinstance(um.get("d_factor"), (int, float)) or um["d_factor"] <= 0:
            raise InvalidSoilGridsResponse(f"layer {layer.get('name')} has no valid d_factor")
    return layers


def _convert(raw: Optional[float], d_factor: float) -> Optional[float]:
    if raw is None:
        return None
    try:
        return round(float(raw) / d_factor, 3)
    except (TypeError, ValueError):
        return None


def parse_layers(layers: List[dict]) -> Dict[str, dict]:
    """Normalise SoilGrids layers into {property: {...}} with converted values per depth."""
    out: Dict[str, dict] = {}
    for layer in layers:
        name = layer["name"]
        um = layer.get("unit_measure", {})
        d = float(um["d_factor"])
        info = config.PROPERTY_INFO.get(name, {"label": name, "unit": um.get("target_units")})
        depths = {}
        for dep in layer["depths"]:
            label = dep.get("label")
            vals = dep.get("values") or {}
            mean = _convert(vals.get("mean"), d)
            median = _convert(vals.get("Q0.5"), d)
            q05 = _convert(vals.get("Q0.05"), d)
            q95 = _convert(vals.get("Q0.95"), d)
            unc = vals.get("uncertainty")
            depths[label] = {
                "mean": mean,
                "median": median,
                "q05": q05,
                "q95": q95,
                # SoilGrids uncertainty = (Q0.95 - Q0.05) / Q0.50, stored x10.
                "uncertainty_index": round(unc / 10.0, 2) if isinstance(unc, (int, float)) else None,
                "raw": vals,
            }
        has_data = any(v["mean"] is not None or v["median"] is not None for v in depths.values())
        out[name] = {
            "label": info["label"],
            "unit": info["unit"],
            "original_units": um.get("mapped_units"),
            "target_units": um.get("target_units"),
            "d_factor": d,
            "depths": depths,
            "has_data": has_data,
        }
    return out


def _best(v: dict) -> Optional[float]:
    return v.get("mean") if v.get("mean") is not None else v.get("median")


def weighted_0_30(prop: dict) -> Optional[float]:
    """Thickness-weighted mean over 0-5, 5-15 and 15-30 cm (uses the depths that have data)."""
    total, weight = 0.0, 0.0
    for label, thick in DEPTH_THICKNESS.items():
        v = prop["depths"].get(label)
        if v and _best(v) is not None:
            total += _best(v) * thick
            weight += thick
    return round(total / weight, 3) if weight else None


def build_profile(lat: float, lon: float, properties: Dict[str, dict], failed: List[str],
                  from_cache: bool = False, access: Optional[dict] = None) -> dict:
    """Assemble the normalised soil profile the chatbot uses."""
    with_data = {k: v for k, v in properties.items() if v["has_data"]}
    null_props = sorted(k for k, v in properties.items() if not v["has_data"])
    missing = sorted(set(failed) | set(null_props) | (set(config.PROPERTIES) - set(properties)))

    if not properties and failed:
        status = "unavailable"
    elif not with_data:
        status = "no_data"            # e.g. urban / water / outside the soil mask
    elif missing:
        status = "partial"
    else:
        status = "ok"

    top = {k: weighted_0_30(v) for k, v in with_data.items()}
    topsoil = {k: _best(v["depths"].get("0-5cm", {})) for k, v in with_data.items()}
    texture = usda_texture_class(top.get("sand"), top.get("silt"), top.get("clay"))

    messages = {
        "ok": "Soil properties retrieved from SoilGrids.",
        "partial": "Some soil properties could not be retrieved from SoilGrids: " + ", ".join(missing) + ".",
        "no_data": "SoilGrids has no soil predictions for this exact point (often urban, water or rock areas). Try a nearby farm location.",
        "unavailable": "SoilGrids could not be reached right now, so no soil data is available.",
    }
    message = messages[status]
    access = access or {}
    dist = access.get("nearest_cell_distance_m")
    if status in ("ok", "partial") and isinstance(dist, (int, float)) and dist > 150:
        message += (f" The exact point has no soil prediction (urban, water or rock), so values are for the "
                    f"nearest mapped 250 m soil cell, about {round(dist / 10) * 10:.0f} m away.")
    if status == "no_data" and access.get("search_radius_m"):
        message = (f"SoilGrids has no soil predictions within about {access['search_radius_m'] / 1000:.0f} km of this point "
                   "(urban, water or rock area). Choose a farm location to get soil data.")
    return {
        "status": status,
        "message": message,
        "access": access,
        "source": config.SOURCE_NAME,
        "location": {"lat": round(lat, 5), "lon": round(lon, 5)},
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "from_cache": from_cache,
        "depths": list(config.DEPTHS),
        "properties": with_data,
        "summary_0_30cm": top,
        "topsoil_0_5cm": topsoil,
        "derived": {
            "texture_class_0_30cm": texture,
            "texture_method": "USDA texture triangle from SoilGrids sand/silt/clay (0-30 cm weighted mean)" if texture else None,
            "ph_class_0_30cm": ph_class(top.get("phh2o")),
            "organic_carbon_class": organic_carbon_class(top.get("soc")),
            "screening_flags": screening_flags(top, texture),
        },
        "missing_properties": missing,
        "not_provided_by_soilgrids": list(config.NOT_PROVIDED),
        "notes": [
            "SoilGrids values are machine-learning predictions for a ~250 m area, not measurements of a specific field.",
            "q05/q95 give the 90% prediction interval; uncertainty_index = (Q95 - Q05) / median (higher = less certain).",
        ],
    }
