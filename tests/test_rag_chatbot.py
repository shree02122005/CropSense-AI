"""
Tests for the SoilGrids-powered RAG chatbot.

    .venv\\Scripts\\python -m pytest tests/test_rag_chatbot.py -v            # offline (no network, no API key)
    .venv\\Scripts\\python -m pytest tests/test_rag_chatbot.py -v -m live    # also hits the real SoilGrids API

Covers: SoilGrids parsing/normalisation, retries / batching / caching / outages,
semantic retrieval, prompt grounding (soil + documents reach the LLM), multi-turn
memory, and "never invent unavailable measurements".
"""
import asyncio
import copy
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.soilgrids import cache as sg_cache, config as sg_config            # noqa: E402
from backend.soilgrids.client import SoilGridsUnavailable                       # noqa: E402
from backend.soilgrids.parser import build_profile, parse_layers, validate_response  # noqa: E402
from backend.soilgrids.service import get_soil_profile                          # noqa: E402
from backend.soilgrids.interpret import usda_texture_class                     # noqa: E402
from backend.rag import llm, pipeline, prompts                                  # noqa: E402
from backend.rag.memory import SessionStore                                     # noqa: E402
from backend.rag.retriever import retrieve, search                              # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
SAMPLE = json.load(open(os.path.join(FIX, "soilgrids_sample.json"), encoding="utf-8"))
NODATA = json.load(open(os.path.join(FIX, "soilgrids_nodata.json"), encoding="utf-8"))
LAT, LON = 15.8497, 74.4977


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(sg_config, "CACHE_PATH", str(tmp_path / "sg_cache.json"))
    monkeypatch.setattr(sg_config, "BACKOFF_BASE_S", 0.01)
    from backend.soilgrids import client as sg_client
    monkeypatch.setattr(sg_client._limiter, "calls", 10_000)   # fake transport: no fair-use throttling needed
    sg_cache.clear_memory()
    yield
    sg_cache.clear_memory()


def fake_api(payload=SAMPLE, fail_props=(), fail_all=False, calls=None):
    """Fake SoilGrids transport: returns only the requested layers; can simulate failures."""
    async def fetch_json(url, params):
        props = [v for k, v in params if k == "property"]
        if calls is not None:
            calls.append(props)
        if fail_all or any(p in fail_props for p in props):
            raise asyncio.TimeoutError("simulated timeout")
        layers = [copy.deepcopy(l) for l in payload["properties"]["layers"] if l["name"] in props]
        return {"type": "Feature", "properties": {"layers": layers}}
    return fetch_json


# ── 1. SoilGrids parsing ─────────────────────────────────────────────────────
def test_unit_conversion_uses_d_factor_and_keeps_original_units():
    props = parse_layers(validate_response(SAMPLE))
    ph = props["phh2o"]["depths"]["0-5cm"]
    assert ph["mean"] == 6.2 and ph["q05"] == 4.7 and ph["q95"] == 8.7
    assert props["phh2o"]["original_units"] == "pH*10"
    assert props["clay"]["depths"]["0-5cm"]["mean"] == 29.8           # 298 g/kg -> 29.8 %
    assert props["nitrogen"]["depths"]["0-5cm"]["mean"] == 1.5        # 150 cg/kg -> 1.5 g/kg
    assert props["bdod"]["depths"]["0-5cm"]["mean"] == 1.3            # 130 cg/cm3 -> 1.3 kg/dm3
    assert props["clay"]["depths"]["0-5cm"]["uncertainty_index"] == 4.2
    assert props["clay"]["depths"]["0-5cm"]["raw"]["mean"] == 298     # raw values preserved


def test_profile_derivations_and_unavailable_parameters():
    profile = build_profile(LAT, LON, parse_layers(validate_response(SAMPLE)), [])
    assert profile["status"] == "ok"
    assert profile["derived"]["texture_class_0_30cm"] == "Clay loam"
    assert profile["derived"]["ph_class_0_30cm"] in ("slightly acidic", "neutral")
    not_provided = " ".join(profile["not_provided_by_soilgrids"]).lower()
    for term in ("phosphorus", "potassium", "moisture"):
        assert term in not_provided
    assert "phosphorus" not in profile["properties"] and "potassium" not in profile["properties"]


def test_texture_triangle_reference_points():
    assert usda_texture_class(90, 5, 5) == "Sand"
    assert usda_texture_class(40, 40, 20) == "Loam"
    assert usda_texture_class(20, 20, 60) == "Clay"
    assert usda_texture_class(65, 20, 15) == "Sandy loam"
    assert usda_texture_class(10, 60, 30) == "Silty clay loam"


def test_malformed_response_rejected():
    from backend.soilgrids.parser import InvalidSoilGridsResponse
    with pytest.raises(InvalidSoilGridsResponse):
        validate_response({"properties": {"layers": [{"name": "phh2o", "depths": [], "unit_measure": {}}]}})


# ── 2. SoilGrids client reliability ──────────────────────────────────────────
def test_batching_caching_and_refresh():
    calls = []
    p1 = run(get_soil_profile(LAT, LON, fetch_json=fake_api(calls=calls), use_rate_limit=False))
    assert p1["status"] == "ok" and len(calls) == 3                     # 9 properties / batch of 3
    p2 = run(get_soil_profile(LAT, LON, fetch_json=fake_api(calls=calls), use_rate_limit=False))
    assert p2["from_cache"] and len(calls) == 3                          # served from cache
    run(get_soil_profile(LAT, LON, refresh=True, fetch_json=fake_api(calls=calls), use_rate_limit=False))
    assert len(calls) == 6                                               # explicit refresh refetches


def test_partial_failure_splits_batch_and_marks_missing():
    calls = []
    p = run(get_soil_profile(LAT, LON, fetch_json=fake_api(fail_props={"cec"}, calls=calls), use_rate_limit=False))
    assert p["status"] == "partial"
    assert p["missing_properties"] == ["cec"]
    assert "bdod" in p["properties"] and "cfvo" in p["properties"]      # siblings recovered by splitting the batch
    assert "cec" not in p["properties"]


def test_outage_returns_no_soil_values():
    p = run(get_soil_profile(LAT, LON, fetch_json=fake_api(fail_all=True), use_rate_limit=False))
    assert p["status"] == "unavailable"
    assert p["properties"] == {} and all(v is None for v in p["summary_0_30cm"].values())
    assert sg_cache.get(LAT, LON) is None                                # failures are not cached


def test_no_data_location():
    p = run(get_soil_profile(LAT, LON, fetch_json=fake_api(payload=NODATA), use_rate_limit=False))
    assert p["status"] == "no_data" and p["properties"] == {}


# ── 2b. WCS access (maps.isric.org) — used first because the REST API is often down ──
def test_wcs_geotiff_decoding_matches_rest_value():
    from backend.soilgrids.wcs import _Grid
    with open(os.path.join(FIX, "wcs_phh2o_0-5cm_mean_belagavi.tif"), "rb") as f:
        g = _Grid(f.read())
    # Same point and layer as the REST fixture: REST returned 62 (pH 6.2) for phh2o 0-5cm mean.
    # WCS output is reprojected to EPSG:4326, so the point can fall in a neighbouring cell (±0.1 pH).
    assert abs(g.value_at(LAT, LON) - 62) <= 1
    assert g.a.shape[0] > 5 and g.a.shape[1] > 5


def test_wcs_nearest_mapped_cell_when_point_is_urban():
    from backend.soilgrids.wcs import NODATA, _Grid, _pick_cell
    with open(os.path.join(FIX, "wcs_phh2o_0-5cm_mean_belagavi.tif"), "rb") as f:
        g = _Grid(f.read())
    r, c = g.rc(LAT, LON)
    g.a[max(0, r - 2):r + 3, max(0, c - 2):c + 3] = NODATA            # simulate a city block around the point
    lat, lon, dist = _pick_cell(g, None, LAT, LON)
    assert dist > 300 and g.value_at(lat, lon) not in (None, NODATA)
    g.a[:, :] = NODATA                                                   # whole window unmapped
    assert _pick_cell(g, None, LAT, LON) is None


def test_access_fallback_wcs_then_rest(monkeypatch):
    from backend.soilgrids import service
    from backend.soilgrids.wcs import WCSUnavailable

    async def wcs_down(lat, lon):
        raise WCSUnavailable("simulated")
    monkeypatch.setattr(service, "_via_wcs", wcs_down)
    p = run(service._fetch_and_build(LAT, LON, fake_api(), False, methods=["wcs", "rest"]))
    assert p["status"] == "ok" and p["access"]["method"] == "SoilGrids REST API v2.0"


def test_nearest_cell_distance_is_disclosed():
    profile = build_profile(LAT, LON, parse_layers(validate_response(SAMPLE)), [],
                            access={"method": "SoilGrids WCS (maps.isric.org)", "nearest_cell_distance_m": 1440})
    assert "nearest mapped 250 m soil cell" in profile["message"] and "1440 m" in profile["message"]


# ── 3. Semantic retrieval ────────────────────────────────────────────────────
@pytest.mark.parametrize("query,expected", [
    ("Can I grow tomatoes here?", "06_crops"),
    ("What fertilizer dose for maize?", "07_fertilizer"),
    ("How do I correct acidic soil?", "09_soil_improvement"),
    ("Does SoilGrids provide available potassium?", "01_soilgrids"),
    ("मिट्टी की जांच कैसे करवाएं?", "11_soil_testing"),
    ("ಕಪ್ಪು ಮಣ್ಣಿನಲ್ಲಿ ಯಾವ ಬೆಳೆ ಬೆಳೆಯಬಹುದು?", "03_indian_soil_types"),
])
def test_retrieval_relevance(query, expected):
    top = [h["source"] for h in search(query, k=4)]
    assert any(expected in s for s in top), top


# ── 4. Pipeline: grounding + memory (LLM stubbed) ────────────────────────────
class StubLLM:
    def __init__(self):
        self.calls = []

    async def __call__(self, system, turns, fallback_lang, provider=None):
        self.calls.append({"system": system, "turns": turns})
        return {"language": "en", "reply": "Stub answer.", "used_soil_data": True,
                "crop_recommendations": [{"crop": "Cotton", "suitability": "good", "reasons": ["clay loam"], "cautions": []}],
                "cited_sources": ["K1", "K99"]}


@pytest.fixture
def stub_llm(monkeypatch):
    stub = StubLLM()
    monkeypatch.setattr(llm, "generate", stub)
    return stub


def test_llm_receives_soil_data_and_retrieved_documents(stub_llm):
    store = SessionStore(); s = store.get(None)
    run(pipeline.set_location(s, LAT, LON, "Belagavi", fetch_json=fake_api()))
    out = run(pipeline.answer(s, "Which crops can I grow here?", "en", provider="gemini"))
    prompt = stub_llm.calls[-1]["turns"][-1]["content"]
    assert "[SOIL DATA]" in prompt and "status: ok" in prompt
    assert "Soil pH (in water)" in prompt and "Clay loam" in prompt
    assert "K1 |" in prompt and "[KNOWLEDGE]" in prompt                  # retrieved excerpts present
    assert "NOT provided by SoilGrids" in prompt
    assert [x["id"] for x in out["sources"]] == ["K1"]                   # invalid citation K99 dropped
    assert out["soil"]["status"] == "ok" and out["crops"][0]["crop"] == "Cotton"


def test_multi_turn_keeps_soil_context_without_asking_location(stub_llm):
    store = SessionStore(); s = store.get(None)
    run(pipeline.set_location(s, LAT, LON, "Belagavi", fetch_json=fake_api()))
    run(pipeline.answer(s, "Which crops can I grow here?", "en", provider="gemini"))
    run(pipeline.answer(s, "Why did you recommend that crop?", "en", provider="gemini"))
    turns = stub_llm.calls[-1]["turns"]
    assert [t["role"] for t in turns] == ["user", "assistant", "user"]
    assert turns[0]["content"] == "Which crops can I grow here?"          # history stores the plain question
    assert "Clay loam" in turns[-1]["content"]                           # soil still in context on follow-up
    assert s.last_crops == ["Cotton"]


def test_location_change_refreshes_soil(stub_llm):
    calls = []
    store = SessionStore(); s = store.get(None)
    run(pipeline.set_location(s, LAT, LON, fetch_json=fake_api(calls=calls)))
    run(pipeline.set_location(s, LAT, LON, fetch_json=fake_api(calls=calls)))          # same place: no refetch
    assert len(calls) == 3
    run(pipeline.set_location(s, 12.97, 77.59, fetch_json=fake_api(calls=calls)))      # new place: refetch
    assert len(calls) == 6 and s.location["lat"] == 12.97


def test_unavailable_soil_is_stated_and_no_values_reach_the_llm(stub_llm):
    store = SessionStore(); s = store.get(None)
    run(pipeline.set_location(s, LAT, LON, fetch_json=fake_api(fail_all=True)))
    run(pipeline.answer(s, "What is my soil pH?", "en", provider="gemini"))
    soil_section = stub_llm.calls[-1]["turns"][-1]["content"].split("[APP ANALYSIS]")[0]
    assert "status: unavailable" in soil_section
    assert "Soil pH (in water)" not in soil_section
    assert not re.search(r"0-30cm \d", soil_section)                     # no numeric soil values at all


def test_district_npk_labelled_as_reference_not_measurement(stub_llm):
    store = SessionStore(); s = store.get(None)
    run(pipeline.answer(s, "What fertilizer should I use?", "en", provider="gemini",
                        analysis={"soil_type": "Black", "N": 249.7, "P": 46.8, "K": 180.4, "npk_district": "Belagavi"}))
    prompt = stub_llm.calls[-1]["turns"][-1]["content"]
    assert "NOT this field's test" in prompt and "status: not_requested" in prompt


def test_system_prompt_forbids_inventing_measurements():
    sp = prompts.SYSTEM_PROMPT.lower()
    assert "never invent" in sp and "available phosphorus" in sp and "soil test" in sp


def test_offline_mode_returns_evidence_only():
    store = SessionStore(); s = store.get(None)
    run(pipeline.set_location(s, LAT, LON, fetch_json=fake_api()))
    out = run(pipeline.answer(s, "How can I improve my soil?", "en", provider="offline"))
    assert out["provider"] == "offline" and "SoilGrids estimate" in out["reply"]
    assert "potassium" not in out["reply"].lower().split("knowledge base")[0]   # no K value claimed from SoilGrids


# ── 5. Live SoilGrids (opt-in: pytest -m live) ───────────────────────────────
@pytest.mark.live
def test_live_soilgrids_wcs_belagavi():
    from backend.soilgrids import service
    p = run(service._fetch_and_build(LAT, LON, service.httpx_fetch_json, True, methods=["wcs"]))
    assert p["status"] in ("ok", "partial") and p["access"]["method"].startswith("SoilGrids WCS")
    assert p["properties"]["phh2o"]["depths"]["0-5cm"]["mean"] == 6.2   # same value as the REST API


@pytest.mark.live
def test_live_soilgrids_bengaluru_rural():
    p = run(get_soil_profile(13.07, 77.50, refresh=True))      # farmland north of Bengaluru
    assert p["status"] in ("ok", "partial", "no_data", "unavailable")
    if p["status"] in ("ok", "partial"):
        ph = p["summary_0_30cm"].get("phh2o")
        assert ph is None or 3.5 <= ph <= 10
    else:
        assert p["properties"] == {}
