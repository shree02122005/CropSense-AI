"""
Configurable LLM providers. All return the same structured answer dict:

    {"language": "kn", "reply": "...", "crop_recommendations": [...],
     "cited_sources": ["K1", ...], "used_soil_data": true}

LLM_PROVIDER=auto picks Gemini if GEMINI_API_KEY is set (free tier), else Claude if
ANTHROPIC_API_KEY is set, else the offline extractive mode (no AI, no cost).
"""
import asyncio
import json
import os
from typing import List, Optional

from pydantic import BaseModel, Field

from . import config


class LLMError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


# ── Structured output schema ─────────────────────────────────────────────────
class CropRecommendation(BaseModel):
    crop: str = Field(description="Crop name in the reply language")
    suitability: str = Field(description="one of: good, possible, not_recommended")
    reasons: List[str] = Field(description="Short reasons grounded in the soil data / knowledge excerpts")
    cautions: List[str] = Field(description="Short cautions or things to check; may be empty")


class ChatAnswer(BaseModel):
    language: str = Field(description="Language code of the reply: en, hi, kn, te, ta, ml, mr, bn, gu, pa or or")
    reply: str = Field(description="Plain-text answer (no markdown) shown on screen and read aloud")
    crop_recommendations: List[CropRecommendation] = Field(description="Only when crops are recommended or assessed; else empty")
    cited_sources: List[str] = Field(description="IDs of knowledge excerpts used, e.g. ['K1','K3']")
    used_soil_data: bool = Field(description="True if SoilGrids values were used in the answer")


ANTHROPIC_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string", "enum": config.LANG_CODES},
        "reply": {"type": "string"},
        "crop_recommendations": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "crop": {"type": "string"},
                "suitability": {"type": "string", "enum": ["good", "possible", "not_recommended"]},
                "reasons": {"type": "array", "items": {"type": "string"}},
                "cautions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["crop", "suitability", "reasons", "cautions"],
            "additionalProperties": False,
        }},
        "cited_sources": {"type": "array", "items": {"type": "string"}},
        "used_soil_data": {"type": "boolean"},
    },
    "required": ["language", "reply", "crop_recommendations", "cited_sources", "used_soil_data"],
    "additionalProperties": False,
}


def provider_name() -> str:
    p = config.LLM_PROVIDER
    if p in ("gemini", "anthropic", "offline"):
        return p
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "offline"


def _coerce(data: dict, fallback_lang: str) -> dict:
    ans = ChatAnswer.model_validate({
        "language": data.get("language") if data.get("language") in config.LANG_CODES else fallback_lang,
        "reply": str(data.get("reply", "")).strip(),
        "crop_recommendations": data.get("crop_recommendations") or [],
        "cited_sources": data.get("cited_sources") or [],
        "used_soil_data": bool(data.get("used_soil_data")),
    })
    if not ans.reply:
        raise LLMError("failed", "Empty reply from the model.")
    return ans.model_dump()


# ── Gemini (free tier available) ─────────────────────────────────────────────
_gemini_client = None


def _gemini_generate(system: str, turns: List[dict], fallback_lang: str) -> dict:
    global _gemini_client
    from google import genai
    from google.genai import errors, types

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise LLMError("not_configured", "GEMINI_API_KEY is not set.")
    if _gemini_client is None:
        _gemini_client = genai.Client(api_key=key)
    contents = [types.Content(role="model" if t["role"] == "assistant" else "user", parts=[types.Part(text=t["content"])])
                for t in turns]
    try:
        resp = _gemini_client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=ChatAnswer,
            ),
        )
    except errors.ClientError as e:
        code = getattr(e, "code", None)
        if code == 429:
            raise LLMError("busy", "Gemini free-tier rate limit reached. Please wait a minute.")
        if code in (401, 403):
            raise LLMError("not_configured", "Invalid GEMINI_API_KEY.")
        if code == 404:
            raise LLMError("failed", f"Gemini model '{config.GEMINI_MODEL}' not found; set GEMINI_MODEL in backend/.env.")
        raise LLMError("failed", f"Gemini request error ({code}).")
    except errors.ServerError:
        raise LLMError("failed", "Gemini service error. Please try again.")
    parsed = getattr(resp, "parsed", None)
    if isinstance(parsed, BaseModel):
        return _coerce(parsed.model_dump(), fallback_lang)
    try:
        return _coerce(json.loads(resp.text or ""), fallback_lang)
    except (json.JSONDecodeError, TypeError):
        raise LLMError("failed", "Gemini returned an unreadable answer.")


# ── Anthropic Claude (paid) ──────────────────────────────────────────────────
_anthropic_client = None


async def _anthropic_generate(system: str, turns: List[dict], fallback_lang: str) -> dict:
    global _anthropic_client
    import anthropic

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise LLMError("not_configured", "ANTHROPIC_API_KEY is not set.")
    if _anthropic_client is None:
        _anthropic_client = anthropic.AsyncAnthropic(timeout=config.LLM_TIMEOUT_S)
    try:
        resp = await _anthropic_client.beta.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=8000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": t["role"], "content": t["content"]} for t in turns],
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": ANTHROPIC_SCHEMA}},
        )
    except anthropic.AuthenticationError:
        raise LLMError("not_configured", "Invalid ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise LLMError("busy", "Too many requests. Please try again shortly.")
    except anthropic.APIStatusError as e:
        raise LLMError("failed", f"AI service error ({e.status_code}).")
    except anthropic.APIConnectionError:
        raise LLMError("failed", "Could not reach the AI service.")
    if resp.stop_reason == "refusal":
        raise LLMError("refused", "The model declined to answer.")
    text = next((b.text for b in resp.content if b.type == "text"), "")
    try:
        return _coerce(json.loads(text), fallback_lang)
    except json.JSONDecodeError:
        raise LLMError("failed", "Unreadable answer.")


async def generate(system: str, turns: List[dict], fallback_lang: str, provider: Optional[str] = None) -> dict:
    provider = provider or provider_name()
    if provider == "gemini":
        try:
            return await asyncio.wait_for(asyncio.to_thread(_gemini_generate, system, turns, fallback_lang),
                                          timeout=config.LLM_TIMEOUT_S)
        except asyncio.TimeoutError:
            raise LLMError("failed", "The AI service took too long to answer.")
    if provider == "anthropic":
        return await _anthropic_generate(system, turns, fallback_lang)
    raise LLMError("offline", "No LLM provider configured.")
