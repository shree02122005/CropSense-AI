"""
Query pipeline for one chat turn:

  1. understand the question (retrieval queries built from message + soil facts + conversation)
  2. load the session's soil information (SoilGrids, refreshed when the location changes)
  3. semantic retrieval from the vector store
  4. combine soil data + app analysis + retrieved knowledge + history
  5. LLM call with grounding rules and structured output
  6. validate citations, update session memory, return a UI-ready payload
"""
import asyncio
from typing import Optional

from backend.soilgrids import get_soil_profile, soil_summary_for_ui

from . import config, llm, prompts
from .memory import Session
from .retriever import retrieve


async def set_location(session: Session, lat: float, lon: float, name: Optional[str] = None,
                       refresh: bool = False, fetch_json=None) -> dict:
    """Store the location and (re)load SoilGrids data when it changed or refresh is requested."""
    changed = session.location_changed(lat, lon)
    session.location = {"lat": lat, "lon": lon, "name": name or (session.location or {}).get("name")}
    if changed or refresh or session.soil_profile is None or session.soil_profile.get("status") == "unavailable":
        kwargs = {"fetch_json": fetch_json} if fetch_json else {}
        session.soil_profile = await get_soil_profile(lat, lon, refresh=refresh, **kwargs)
        if changed:
            session.last_crops = []
    return session.soil_profile


def _offline_answer(message: str, session: Session, hits: list, ui_language: str) -> dict:
    """No-LLM mode: return the evidence itself (soil summary + best excerpts). Never generates claims."""
    parts = []
    p = session.soil_profile
    if p and p["status"] in ("ok", "partial"):
        s, d = p["summary_0_30cm"], p["derived"]
        bits = []
        if s.get("phh2o") is not None:
            bits.append(f"pH {s['phh2o']:.1f} ({d.get('ph_class_0_30cm')})")
        if d.get("texture_class_0_30cm"):
            bits.append(f"texture {d['texture_class_0_30cm']}")
        if s.get("soc") is not None:
            bits.append(f"organic carbon {s['soc'] / 10:.2f}% ({d.get('organic_carbon_class')})")
        parts.append("SoilGrids estimate for your location (0-30 cm): " + ", ".join(bits) + ".")
        for f in d.get("screening_flags", [])[:3]:
            parts.append(f"Check: {f['flag']} ({f['evidence']}).")
    elif p:
        parts.append(p["message"])
    else:
        parts.append("Share your location to get soil information for your area.")
    if hits:
        parts.append("Relevant guidance from the knowledge base:")
        for i, h in enumerate(hits[:2], 1):
            body = h["text"].split("\n", 1)[-1].strip()
            parts.append(f"[K{i}] {h['title']} — {h['section']}: {body[:420]}{'…' if len(body) > 420 else ''}")
    parts.append("(Offline mode: AI answer generation is not configured, so this shows the retrieved evidence in English.)")
    return {"language": "en", "reply": "\n".join(parts), "crop_recommendations": [],
            "cited_sources": [f"K{i}" for i in range(1, min(2, len(hits)) + 1)], "used_soil_data": bool(p and p["status"] in ("ok", "partial"))}


async def answer(session: Session, message: str, ui_language: str = "en",
                 analysis: Optional[dict] = None, provider: Optional[str] = None) -> dict:
    if analysis:
        session.analysis = analysis
    ui_language = ui_language if ui_language in config.LANG_CODES else "en"

    # 3. semantic retrieval (CPU-bound embedding -> thread)
    hits = await asyncio.to_thread(retrieve, message, session.soil_profile, session.analysis,
                                   session.history, session.last_crops)

    # 4-5. combine + generate
    provider = provider or llm.provider_name()
    if provider == "offline":
        result = _offline_answer(message, session, hits, ui_language)
    else:
        turns = [dict(t) for t in session.history[-config.MAX_HISTORY_TURNS * 2:]]
        while turns and turns[0]["role"] != "user":
            turns.pop(0)
        turns.append({"role": "user", "content": prompts.user_turn(
            message, ui_language, session.soil_profile, session.location, session.analysis, hits)})
        result = await llm.generate(prompts.SYSTEM_PROMPT, turns, ui_language, provider=provider)

    # 6. validate citations against what was actually retrieved
    valid_ids = {f"K{i}" for i in range(1, len(hits) + 1)}
    cited = [c for c in result["cited_sources"] if c in valid_ids]
    sources = []
    for c in cited:
        h = hits[int(c[1:]) - 1]
        sources.append({"id": c, "title": h["title"], "section": h["section"], "file": h["source"], "score": h["score"]})

    # memory: store the plain question (not the evidence block) and the answer
    session.add_turn(message, result["reply"])
    if result["crop_recommendations"]:
        session.last_crops = [c["crop"] for c in result["crop_recommendations"]]
    session.last_sources = sources

    return {
        "session_id": session.id,
        "language": result["language"],
        "reply": result["reply"],
        "crops": result["crop_recommendations"],
        "sources": sources,
        "used_soil_data": result["used_soil_data"],
        "soil": soil_summary_for_ui(session.soil_profile),
        "location": session.location,
        "provider": provider,
        "retrieved": [{"id": f"K{i}", "chunk": h["id"], "score": h["score"]} for i, h in enumerate(hits, 1)],
    }
