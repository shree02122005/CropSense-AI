"""Small JSON-file cache for SoilGrids profiles (keyed by rounded coordinates)."""
import json
import os
import threading
import time
from typing import Optional

from . import config

_lock = threading.Lock()
_mem: dict = {}
_loaded = False


def key_for(lat: float, lon: float) -> str:
    return f"{round(lat, config.COORD_PRECISION):.{config.COORD_PRECISION}f},{round(lon, config.COORD_PRECISION):.{config.COORD_PRECISION}f}"


def _load():
    global _loaded, _mem
    if _loaded:
        return
    try:
        with open(config.CACHE_PATH, encoding="utf-8") as f:
            _mem = json.load(f)
    except (OSError, ValueError):
        _mem = {}
    _loaded = True


def get(lat: float, lon: float) -> Optional[dict]:
    with _lock:
        _load()
        entry = _mem.get(key_for(lat, lon))
        if not entry:
            return None
        if time.time() > entry.get("expires_at", 0):
            return None
        return entry["profile"]


def put(lat: float, lon: float, profile: dict):
    if profile.get("status") not in ("ok", "partial", "no_data"):
        return                                   # never cache failures
    ttl = {"ok": config.CACHE_TTL_S, "no_data": 24 * 3600}.get(profile["status"], config.PARTIAL_CACHE_TTL_S)
    with _lock:
        _load()
        _mem[key_for(lat, lon)] = {"expires_at": time.time() + ttl, "profile": profile}
        try:
            os.makedirs(os.path.dirname(config.CACHE_PATH), exist_ok=True)
            tmp = config.CACHE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(_mem, f)
            os.replace(tmp, config.CACHE_PATH)
        except OSError:
            pass                                 # cache is best-effort


def clear_memory():
    """For tests."""
    global _mem, _loaded
    with _lock:
        _mem, _loaded = {}, True
