"""
Alternative official access: ISRIC SoilGrids Web Coverage Service (maps.isric.org).

The REST API (rest.isric.org) is a beta service and is regularly unreachable; the
WCS serves the same SoilGrids 2.0 maps. We request a small GeoTIFF window around the
point (EPSG:4326), read it with Pillow, and return layers in the SAME JSON shape as
the REST API so the parser/interpretation code is shared.

Urban, water and rock pixels have no prediction. If the exact cell is empty we use
the nearest mapped cell inside the window and report how far away it is.
"""
import asyncio
import io
import math
from typing import Dict, List, Optional, Tuple

import httpx
import numpy as np
from PIL import Image

from . import config

WCS_URL = "https://maps.isric.org/mapserv"
CRS_4326 = "http://www.opengis.net/def/crs/EPSG/0/4326"
WINDOW_DEG = float(__import__("os").getenv("SOILGRIDS_WCS_WINDOW_DEG", "0.02"))   # ±0.02° ≈ ±2 km
CONCURRENCY = int(__import__("os").getenv("SOILGRIDS_WCS_CONCURRENCY", "8"))
WCS_TIMEOUT_S = float(__import__("os").getenv("SOILGRIDS_WCS_TIMEOUT_S", "20"))
STATS = ["mean", "Q0.05", "Q0.95"]          # quantiles keep the 90% prediction interval
NODATA = -32768

# Same unit metadata the REST API returns for each layer.
UNIT_MEASURE = {
    "phh2o":    {"d_factor": 10,  "mapped_units": "pH*10",      "target_units": "-"},
    "clay":     {"d_factor": 10,  "mapped_units": "g/kg",       "target_units": "%"},
    "sand":     {"d_factor": 10,  "mapped_units": "g/kg",       "target_units": "%"},
    "silt":     {"d_factor": 10,  "mapped_units": "g/kg",       "target_units": "%"},
    "nitrogen": {"d_factor": 100, "mapped_units": "cg/kg",      "target_units": "g/kg"},
    "soc":      {"d_factor": 10,  "mapped_units": "dg/kg",      "target_units": "g/kg"},
    "cec":      {"d_factor": 10,  "mapped_units": "mmol(c)/kg", "target_units": "cmol(c)/kg"},
    "bdod":     {"d_factor": 100, "mapped_units": "cg/cm³",     "target_units": "kg/dm³"},
    "cfvo":     {"d_factor": 10,  "mapped_units": "cm³/dm³",    "target_units": "cm³/100cm³"},
}
DEPTH_RANGE = {"0-5cm": (0, 5), "5-15cm": (5, 15), "15-30cm": (15, 30)}


class WCSUnavailable(Exception):
    pass


class _Grid:
    """A decoded GeoTIFF window."""
    def __init__(self, data: bytes):
        im = Image.open(io.BytesIO(data))
        tags = im.tag_v2
        scale, tie = tags.get(33550), tags.get(33922)          # ModelPixelScale, ModelTiepoint
        if not scale or not tie:
            raise ValueError("GeoTIFF without georeferencing tags")
        self.a = np.array(im).astype(np.int64)
        self.sx, self.sy = float(scale[0]), float(scale[1])
        self.x0, self.y0 = float(tie[3]), float(tie[4])        # top-left corner (lon, lat)

    def rc(self, lat: float, lon: float) -> Tuple[int, int]:
        return int((self.y0 - lat) / self.sy), int((lon - self.x0) / self.sx)

    def center(self, r: int, c: int) -> Tuple[float, float]:
        return self.y0 - (r + 0.5) * self.sy, self.x0 + (c + 0.5) * self.sx

    def value_at(self, lat: float, lon: float) -> Optional[int]:
        r, c = self.rc(lat, lon)
        if 0 <= r < self.a.shape[0] and 0 <= c < self.a.shape[1]:
            v = int(self.a[r, c])
            return None if v == NODATA else v
        return None


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(a))


async def _coverage(client: httpx.AsyncClient, sem: asyncio.Semaphore, prop: str, depth: str, stat: str,
                    lat: float, lon: float) -> Optional[_Grid]:
    params = [
        ("map", f"/map/{prop}.map"), ("SERVICE", "WCS"), ("VERSION", "2.0.1"), ("REQUEST", "GetCoverage"),
        ("COVERAGEID", f"{prop}_{depth}_{stat}"), ("FORMAT", "image/tiff"),
        ("SUBSET", f"long({lon - WINDOW_DEG:.5f},{lon + WINDOW_DEG:.5f})"),
        ("SUBSET", f"lat({lat - WINDOW_DEG:.5f},{lat + WINDOW_DEG:.5f})"),
        ("SUBSETTINGCRS", CRS_4326), ("OUTPUTCRS", CRS_4326),
    ]
    for attempt in range(config.MAX_RETRIES + 1):
        try:
            async with sem:
                r = await client.get(WCS_URL, params=params)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image/tiff"):
                return _Grid(r.content)
            if 400 <= r.status_code < 500:
                return None                                  # unknown coverage: do not retry
        except (httpx.HTTPError, ValueError, OSError):
            pass
        if attempt < config.MAX_RETRIES:
            await asyncio.sleep(config.BACKOFF_BASE_S * (2 ** attempt))
    return None


def _pick_cell(ph: _Grid, clay: Optional[_Grid], lat: float, lon: float) -> Optional[Tuple[float, float, float]]:
    """Nearest cell with a soil prediction (pH > 0 and texture present). Returns (lat, lon, distance_m)."""
    valid = (ph.a != NODATA) & (ph.a > 0)
    if clay is not None and clay.a.shape == ph.a.shape:
        valid &= (clay.a != NODATA) & (clay.a > 0)
    if not valid.any():
        return None
    rows, cols = np.nonzero(valid)
    best = None
    for r, c in zip(rows.tolist(), cols.tolist()):
        clat, clon = ph.center(r, c)
        d = _haversine_m(lat, lon, clat, clon)
        if best is None or d < best[2]:
            best = (clat, clon, d)
    return best


async def fetch_layers_wcs(lat: float, lon: float, properties: List[str]) -> Tuple[List[dict], List[str], dict]:
    """
    Returns (layers in REST format, failed_properties, access_info).
    Raises WCSUnavailable if the service cannot be used at all.
    """
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(timeout=WCS_TIMEOUT_S, headers={"User-Agent": "CropSenseAI-chatbot/1.0"}) as client:
        # 1. Locate the nearest mapped soil cell using topsoil pH + clay.
        ph_grid, clay_grid = await asyncio.gather(
            _coverage(client, sem, "phh2o", "0-5cm", "mean", lat, lon),
            _coverage(client, sem, "clay", "0-5cm", "mean", lat, lon),
        )
        if ph_grid is None:
            raise WCSUnavailable("SoilGrids WCS did not return data")
        cell = _pick_cell(ph_grid, clay_grid, lat, lon)
        if cell is None:
            # Whole window is urban/water/rock: report no data (layers with null values).
            empty = [{"name": p, "unit_measure": UNIT_MEASURE[p], "depths": [
                {"label": d, "range": {"top_depth": a, "bottom_depth": b, "unit_depth": "cm"},
                 "values": {s: None for s in STATS}} for d, (a, b) in DEPTH_RANGE.items()]} for p in properties]
            return empty, [], {"method": "SoilGrids WCS (maps.isric.org)", "nearest_cell_distance_m": None,
                               "search_radius_m": round(WINDOW_DEG * 111_000)}
        clat, clon, dist = cell

        # 2. Fetch every property/depth/statistic for that cell.
        jobs = [(p, d, s) for p in properties for d in config.DEPTHS for s in STATS]
        grids = await asyncio.gather(*[_coverage(client, sem, p, d, s, lat, lon) for p, d, s in jobs])

    values: Dict[str, Dict[str, Dict[str, Optional[int]]]] = {}
    for (p, d, s), g in zip(jobs, grids):
        values.setdefault(p, {}).setdefault(d, {})[s] = g.value_at(clat, clon) if g is not None else None

    layers, failed = [], []
    for p in properties:
        depths = values.get(p, {})
        if all(depths.get(d, {}).get("mean") is None for d in config.DEPTHS):
            failed.append(p)
            continue
        layers.append({
            "name": p,
            "unit_measure": {**UNIT_MEASURE[p], "uncertainty_unit": ""},
            "depths": [{"label": d, "range": {"top_depth": a, "bottom_depth": b, "unit_depth": "cm"},
                        "values": depths.get(d, {s: None for s in STATS})} for d, (a, b) in DEPTH_RANGE.items()],
        })
    return layers, failed, {
        "method": "SoilGrids WCS (maps.isric.org)",
        "cell_center": {"lat": round(clat, 5), "lon": round(clon, 5)},
        "nearest_cell_distance_m": round(dist),
    }
