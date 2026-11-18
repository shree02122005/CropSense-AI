"""
chat.py — HTTP API for "Krishi Mitra", the SoilGrids-powered RAG agricultural chatbot.

  POST /chat            ask a question (uses the session's location, SoilGrids data, RAG knowledge)
  POST /chat/location   set / change / refresh the session location and load SoilGrids data
  POST /chat/reset      clear the session memory
  GET  /chat/status     provider, knowledge-base index status
  POST /chat/tts        MP3 speech for a reply (gTTS)

Modules: backend/soilgrids (soil data, independent) · backend/rag (retrieval, memory, LLM).
"""
import io
import os
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from backend.rag import ingest, llm, pipeline                 # noqa: E402  (env must be loaded first)
from backend.rag.config import LANG_CODES                      # noqa: E402
from backend.rag.memory import sessions                        # noqa: E402
from backend.soilgrids import soil_summary_for_ui              # noqa: E402

router = APIRouter()
ingest.warm_up_in_background()     # load/build the vector index without blocking startup

MAX_MESSAGE_CHARS = 1000
MAX_TTS_CHARS = 1500


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    name: Optional[str] = Field(default=None, max_length=300)


class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    ui_language: str = "en"
    location: Optional[Location] = None        # optional: sets/changes location in the same call
    refresh_soil: bool = False
    context: Optional[dict] = None             # latest CropSense analysis (whitelisted fields)


class LocationRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    location: Location
    refresh: bool = False


class SessionRequest(BaseModel):
    session_id: str = Field(max_length=64)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TTS_CHARS * 2)
    language: str = "en"


ANALYSIS_FIELDS = ("location", "soil_type", "soil_confidence", "N", "P", "K", "npk_district", "npk_out_of_training_range",
                   "npk_ood_features", "ph", "organic_carbon", "temperature", "humidity", "rainfall")


def _clean_analysis(ctx: Optional[dict]) -> Optional[dict]:
    if not ctx:
        return None
    out = {k: ctx.get(k) for k in ANALYSIS_FIELDS}
    out["crops"] = [{k: c.get(k) for k in ("name", "confidence", "season", "water_need", "profit")}
                    for c in (ctx.get("crops") or [])[:3] if isinstance(c, dict)]
    return out


def _http_error(e: llm.LLMError):
    status = {"not_configured": 503, "busy": 429, "refused": 200}.get(e.code, 502)
    raise HTTPException(status_code=status, detail={"code": e.code, "message": str(e)})


@router.post("/chat")
async def chat(req: ChatRequest):
    session = sessions.get(req.session_id)
    if req.location:
        await pipeline.set_location(session, req.location.lat, req.location.lon, req.location.name, req.refresh_soil)
    elif req.refresh_soil and session.location:
        await pipeline.set_location(session, session.location["lat"], session.location["lon"], refresh=True)
    try:
        return await pipeline.answer(session, req.message.strip(),
                                     req.ui_language if req.ui_language in LANG_CODES else "en",
                                     analysis=_clean_analysis(req.context))
    except llm.LLMError as e:
        if e.code == "refused":
            return {"session_id": session.id, "reply": None, "code": "refused", "language": req.ui_language}
        _http_error(e)


@router.post("/chat/location")
async def chat_location(req: LocationRequest):
    session = sessions.get(req.session_id)
    profile = await pipeline.set_location(session, req.location.lat, req.location.lon, req.location.name, req.refresh)
    return {"session_id": session.id, "location": session.location, "soil": soil_summary_for_ui(profile)}


@router.post("/chat/reset")
def chat_reset(req: SessionRequest):
    sessions.reset(req.session_id)
    return {"ok": True}


@router.get("/chat/status")
def chat_status():
    return {"provider": llm.provider_name(), "knowledge_index_ready": ingest.is_ready()}


# gTTS language codes (Odia is not supported by gTTS; the browser voice is used for it when available).
GTTS_LANGS = {"en": "en", "hi": "hi", "kn": "kn", "te": "te", "ta": "ta", "ml": "ml",
              "mr": "mr", "bn": "bn", "gu": "gu", "pa": "pa"}


@router.post("/chat/tts")
def chat_tts(req: TTSRequest):
    lang = GTTS_LANGS.get(req.language)
    if not lang:
        raise HTTPException(status_code=422, detail={"code": "voice_unavailable", "message": f"No voice for '{req.language}'."})
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=req.text[:MAX_TTS_CHARS], lang=lang, tld="co.in" if lang == "en" else "com").write_to_fp(buf)
        buf.seek(0)
    except Exception as e:
        raise HTTPException(status_code=502, detail={"code": "voice_failed", "message": f"Speech generation failed: {type(e).__name__}"})
    return StreamingResponse(buf, media_type="audio/mpeg")
