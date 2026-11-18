"""
HTTP access to the SoilGrids REST API (beta service: slow and sometimes down).

- Per-request timeout, retries with exponential backoff + jitter.
- Client-side rate limiter (ISRIC fair use: ~5 requests/minute).
- Properties fetched in small batches; a batch that keeps failing is split into
  single-property requests so one slow layer does not lose all the others.

The transport is a plain function argument (`fetch_json`) so tests can inject a
fake, and so another official access method (e.g. WCS/WebDAV GeoTIFFs) can be
plugged in later without touching the parser or the chatbot.
"""
import asyncio
import random
import time
from collections import deque
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

import httpx

from . import config

FetchJson = Callable[[str, list], Awaitable[dict]]


class SoilGridsUnavailable(Exception):
    """SoilGrids could not be reached / kept failing after retries."""


class _RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls, self.period = calls, period
        self._stamps = deque()
        self._lock = asyncio.Lock()

    async def acquire(self, deadline: float):
        async with self._lock:
            while True:
                now = time.monotonic()
                while self._stamps and now - self._stamps[0] >= self.period:
                    self._stamps.popleft()
                if len(self._stamps) < self.calls:
                    self._stamps.append(now)
                    return
                wait = self.period - (now - self._stamps[0]) + 0.05
                if now + wait > deadline:
                    raise SoilGridsUnavailable("rate limit wait would exceed the time budget")
                await asyncio.sleep(wait)


_limiter = _RateLimiter(config.RATE_LIMIT_CALLS, config.RATE_LIMIT_PERIOD_S)


async def httpx_fetch_json(url: str, params: list) -> dict:
    """Default transport: one GET with a timeout. Raises on non-200 / bad JSON."""
    async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT_S,
                                 headers={"Accept": "application/json", "User-Agent": "CropSenseAI-chatbot/1.0"}) as client:
        r = await client.get(url, params=params)
    if r.status_code == 429:
        raise httpx.HTTPStatusError("rate limited", request=r.request, response=r)
    r.raise_for_status()
    return r.json()


def _params(lat: float, lon: float, props: List[str]) -> list:
    p = [("lon", f"{lon:.5f}"), ("lat", f"{lat:.5f}")]
    p += [("property", x) for x in props]
    p += [("depth", d) for d in config.DEPTHS]
    p += [("value", v) for v in config.VALUES]
    return p


async def _fetch_batch(lat, lon, props, fetch_json: FetchJson, deadline: float,
                       limiter: Optional[_RateLimiter]) -> dict:
    url = config.BASE_URL + config.QUERY_PATH
    last_err: Optional[Exception] = None
    for attempt in range(config.MAX_RETRIES + 1):
        if time.monotonic() >= deadline:
            break
        try:
            if limiter:
                await limiter.acquire(deadline)
            remaining = max(1.0, deadline - time.monotonic())
            return await asyncio.wait_for(fetch_json(url, _params(lat, lon, props)),
                                          timeout=min(config.REQUEST_TIMEOUT_S, remaining))
        except SoilGridsUnavailable:
            raise
        except httpx.HTTPStatusError as e:
            last_err = e
            if e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                break                      # bad request: retrying will not help
        except Exception as e:             # timeout, connection error, bad JSON
            last_err = e
        if attempt < config.MAX_RETRIES:
            delay = config.BACKOFF_BASE_S * (2 ** attempt) + random.uniform(0, 0.5)
            if time.monotonic() + delay >= deadline:
                break
            await asyncio.sleep(delay)
    raise SoilGridsUnavailable(f"{','.join(props)}: {type(last_err).__name__ if last_err else 'time budget exceeded'}")


async def fetch_properties(lat: float, lon: float, properties: List[str],
                           fetch_json: FetchJson = httpx_fetch_json,
                           budget_s: float = config.TOTAL_BUDGET_S,
                           use_rate_limit: bool = True) -> Tuple[List[dict], List[str]]:
    """
    Fetch the requested properties. Returns (layers, failed_properties).
    Raises SoilGridsUnavailable only if NOTHING could be retrieved.
    """
    deadline = time.monotonic() + budget_s
    limiter = _limiter if use_rate_limit else None
    layers: Dict[str, dict] = {}
    failed: List[str] = []
    batches = [properties[i:i + config.BATCH_SIZE] for i in range(0, len(properties), config.BATCH_SIZE)]

    for batch in batches:
        try:
            payload = await _fetch_batch(lat, lon, batch, fetch_json, deadline, limiter)
            for layer in (payload.get("properties") or {}).get("layers", []) or []:
                layers[layer.get("name")] = layer
            failed += [p for p in batch if p not in layers]
        except SoilGridsUnavailable:
            if len(batch) == 1 or time.monotonic() >= deadline:
                failed += batch
                continue
            for prop in batch:            # split a failing batch into single properties
                try:
                    payload = await _fetch_batch(lat, lon, [prop], fetch_json, deadline, limiter)
                    for layer in (payload.get("properties") or {}).get("layers", []) or []:
                        layers[layer.get("name")] = layer
                    if prop not in layers:
                        failed.append(prop)
                except SoilGridsUnavailable:
                    failed.append(prop)

    if not layers:
        raise SoilGridsUnavailable("no soil properties could be retrieved")
    return list(layers.values()), sorted(set(failed))
