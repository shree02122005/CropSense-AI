"""
Public entry point: get a normalised soil profile for a coordinate.

    profile = await get_soil_profile(lat, lon)            # cached when possible
    profile = await get_soil_profile(lat, lon, refresh=True)

Never raises for network problems: returns a profile with status
"unavailable" and NO soil values, so callers cannot accidentally use invented data.
"""
import asyncio
import os
import time
from typing import Dict, List, Optional

from . import cache, config
from .client import FetchJson, SoilGridsUnavailable, fetch_properties, httpx_fetch_json
from .parser import InvalidSoilGridsResponse, build_profile, parse_layers, validate_response
from .wcs import WCSUnavailable, fetch_layers_wcs

_inflight: Dict[str, asyncio.Task] = {}

# Access methods, tried in order. The WCS (maps.isric.org) is the more reliable official
# endpoint; the REST API (rest.isric.org) is a beta service that is often unreachable.
ACCESS_ORDER = [m.strip() for m in os.getenv("SOILGRIDS_ACCESS_ORDER", "wcs,rest").split(",") if m.strip()]
WCS_BUDGET_S = float(os.getenv("SOILGRIDS_WCS_BUDGET_S", "45"))
REST_COOLDOWN_S = 600            # after REST fails completely, skip it for 10 minutes
_rest_down_until = 0.0


def _valid_coords(lat: float, lon: float) -> bool:
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and -90 <= lat <= 90 and -180 <= lon <= 180


async def _via_wcs(lat: float, lon: float) -> dict:
    layers, failed, access = await asyncio.wait_for(fetch_layers_wcs(lat, lon, list(config.PROPERTIES)), timeout=WCS_BUDGET_S)
    layers = validate_response({"properties": {"layers": layers}})
    return build_profile(lat, lon, parse_layers(layers), failed, access=access)


async def _via_rest(lat: float, lon: float, fetch_json: FetchJson, use_rate_limit: bool) -> dict:
    layers, failed = await fetch_properties(lat, lon, list(config.PROPERTIES),
                                            fetch_json=fetch_json, use_rate_limit=use_rate_limit)
    layers = validate_response({"properties": {"layers": layers}})
    return build_profile(lat, lon, parse_layers(layers), failed, access={"method": "SoilGrids REST API v2.0"})


async def _fetch_and_build(lat: float, lon: float, fetch_json: FetchJson, use_rate_limit: bool,
                           methods: Optional[List[str]] = None) -> dict:
    global _rest_down_until
    # An injected transport (tests, alternative access) means "REST-format transport only".
    if methods is None:
        methods = ACCESS_ORDER if fetch_json is httpx_fetch_json else ["rest"]
    errors = []
    profile = None
    for method in methods:
        try:
            if method == "wcs":
                profile = await _via_wcs(lat, lon)
            elif method == "rest":
                if fetch_json is httpx_fetch_json and time.monotonic() < _rest_down_until:
                    errors.append("rest: skipped (recently unreachable)")
                    continue
                profile = await _via_rest(lat, lon, fetch_json, use_rate_limit)
            else:
                continue
            if profile["status"] in ("ok", "partial", "no_data"):
                break
        except (WCSUnavailable, SoilGridsUnavailable, InvalidSoilGridsResponse, asyncio.TimeoutError) as e:
            errors.append(f"{method}: {type(e).__name__}: {e}")
            if method == "rest" and fetch_json is httpx_fetch_json:
                _rest_down_until = time.monotonic() + REST_COOLDOWN_S
            profile = None
    if profile is None or profile["status"] == "unavailable":
        profile = build_profile(lat, lon, {}, list(config.PROPERTIES))
        profile["error"] = "; ".join(errors) or "no access method succeeded"
    cache.put(lat, lon, profile)
    return profile


async def get_soil_profile(lat: float, lon: float, refresh: bool = False,
                           fetch_json: FetchJson = httpx_fetch_json,
                           use_rate_limit: bool = True) -> dict:
    if not _valid_coords(lat, lon):
        raise ValueError("latitude/longitude out of range")
    if not refresh:
        cached = cache.get(lat, lon)
        if cached:
            return {**cached, "from_cache": True}

    key = cache.key_for(lat, lon)
    task: Optional[asyncio.Task] = _inflight.get(key)
    if task is None or task.done():               # de-duplicate concurrent requests for one point
        task = asyncio.ensure_future(_fetch_and_build(lat, lon, fetch_json, use_rate_limit))
        _inflight[key] = task
    try:
        return await asyncio.shield(task)
    finally:
        if task.done():
            _inflight.pop(key, None)


def soil_summary_for_ui(profile: Optional[dict]) -> Optional[dict]:
    """Compact view for the chat UI card."""
    if not profile:
        return None
    rows = []
    for name in config.PROPERTIES:
        p = profile.get("properties", {}).get(name)
        if not p:
            continue
        rows.append({
            "property": name,
            "label": p["label"],
            "unit": p["unit"],
            "depths": {d: {k: p["depths"].get(d, {}).get(k) for k in ("mean", "q05", "q95")} for d in config.DEPTHS},
        })
    return {
        "status": profile.get("status"),
        "message": profile.get("message"),
        "location": profile.get("location"),
        "from_cache": profile.get("from_cache"),
        "texture_class": profile.get("derived", {}).get("texture_class_0_30cm"),
        "ph_class": profile.get("derived", {}).get("ph_class_0_30cm"),
        "organic_carbon_class": profile.get("derived", {}).get("organic_carbon_class"),
        "flags": profile.get("derived", {}).get("screening_flags", []),
        "rows": rows,
        "missing_properties": profile.get("missing_properties", []),
        "not_provided": profile.get("not_provided_by_soilgrids", []),
        "source": profile.get("source"),
        "access_method": (profile.get("access") or {}).get("method"),
        "nearest_cell_distance_m": (profile.get("access") or {}).get("nearest_cell_distance_m"),
    }
