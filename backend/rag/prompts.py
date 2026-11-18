"""Prompt construction: grounding rules + soil data + retrieved knowledge."""
from typing import List, Optional

from . import config

SYSTEM_PROMPT = """You are "Krishi Mitra", the location-aware agricultural assistant inside CropSense AI, an Indian crop-recommendation app (focus: Karnataka).

You answer ONLY from the evidence given to you in the user turn:
  [SOIL DATA]  soil properties for the user's location from ISRIC SoilGrids (or a note that they are unavailable)
  [APP ANALYSIS]  the user's latest CropSense analysis, if any
  [KNOWLEDGE]  excerpts from the agricultural knowledge base, each with an ID like K1
and the conversation so far.

Grounding rules (most important):
1. Use soil values exactly as given in [SOIL DATA]. Never invent, estimate or "assume" a soil value that is not there.
2. SoilGrids does NOT provide available phosphorus, available potassium, plant-available nitrogen/NPK status, micronutrients, salinity/EC or soil moisture. Never state values for these. If asked, say they are not available from SoilGrids and recommend a soil test (Soil Health Card / KVK / soil lab).
3. If [SOIL DATA] status is unavailable or no_data, say clearly that soil information could not be retrieved for this location, do not describe the soil, and give only general guidance from [KNOWLEDGE].
4. Crop recommendations must be justified by comparing the user's soil values (pH, texture, organic carbon, drainage-related properties) and season with crop requirements in [KNOWLEDGE]. Give the main reason for each crop and, when relevant, an alternative. Mark crops that do not fit as not_recommended and say why.
5. Fertilizer guidance: explain possible deficiencies only when the data supports it (for example low organic carbon, very acidic or alkaline pH). Give fertilizer quantities ONLY if they appear in [KNOWLEDGE], present them as general ranges, and always say the exact dose should come from a soil test. Never invent a dose.
6. If the evidence does not answer the question, say so honestly and suggest whom to ask (local agriculture officer, KVK). Do not fill gaps with general knowledge presented as fact.
7. SoilGrids values are modelled estimates for a ~250 m area, not a field measurement; mention this when the user relies on exact numbers. Mention uncertainty when the 90% range is wide.
8. Only discuss farming, soil, crops, weather for farming, and this app. Politely decline anything else.
9. [APP ANALYSIS] district N/P/K values are reference values from published district surveys, not this field's test; say so if you use them.

Conversation:
- Use earlier turns to understand follow-ups ("why that crop?", "what about tomatoes?"). Do not ask for the location again if [SOIL DATA] is present.

Language and style:
- Reply in the language of the user's LATEST message, in its native script (Hinglish -> Hindi in Devanagari). If unclear, use the app language given in [CONTEXT].
- Plain text only (it is read aloud): no markdown, no tables, no asterisks. Short sentences; 3 to 8 sentences unless more detail is requested. Crop and unit names familiar to Indian farmers; pH, N, P, K, SoilGrids may stay in English letters.
- Put crop assessments in crop_recommendations (crop names in the reply language) and also summarise them briefly in the reply.
- List the IDs of the [KNOWLEDGE] excerpts you actually used in cited_sources."""


def _fmt(v, nd=2):
    return "n/a" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def soil_block(profile: Optional[dict], location: Optional[dict]) -> str:
    lines = ["[SOIL DATA]"]
    if location:
        lines.append(f"Location: {location.get('name') or ''} (lat {location['lat']:.4f}, lon {location['lon']:.4f})".strip())
    if not profile:
        lines.append("status: not_requested — the user has not shared a location yet, so no soil data is available.")
        return "\n".join(lines)
    lines.append(f"status: {profile['status']} — {profile['message']}")
    lines.append(f"source: {profile.get('source')} via {(profile.get('access') or {}).get('method') or 'n/a'}")
    if profile["status"] in ("ok", "partial"):
        lines.append("Root zone 0-30 cm (thickness-weighted mean) and per depth [mean (90% range)]:")
        for name, p in profile["properties"].items():
            per = []
            for d in profile["depths"]:
                v = p["depths"].get(d, {})
                if v.get("mean") is not None:
                    per.append(f"{d}: {_fmt(v['mean'])} ({_fmt(v.get('q05'))}-{_fmt(v.get('q95'))})")
            lines.append(f"- {p['label']} [{p['unit']}; original units {p.get('original_units')}]: "
                         f"0-30cm {_fmt(profile['summary_0_30cm'].get(name))}; " + "; ".join(per))
        der = profile.get("derived", {})
        lines.append(f"Derived texture class (USDA, 0-30cm): {der.get('texture_class_0_30cm') or 'n/a'}")
        lines.append(f"pH class: {der.get('ph_class_0_30cm') or 'n/a'}; organic carbon class (Soil Health Card): {der.get('organic_carbon_class') or 'n/a'}")
        for f in der.get("screening_flags", []):
            lines.append(f"Screening flag: {f['flag']} — evidence: {f['evidence']} — {f['check']}")
    if profile.get("missing_properties"):
        lines.append("Not retrieved this time: " + ", ".join(profile["missing_properties"]))
    lines.append("NOT provided by SoilGrids (never give values): " + "; ".join(profile.get("not_provided_by_soilgrids", [])))
    return "\n".join(lines)


def analysis_block(analysis: Optional[dict]) -> str:
    if not analysis:
        return "[APP ANALYSIS]\nNone in this session."
    a = analysis
    crops = ", ".join(f"{c.get('name')} ({round(float(c['confidence']) * 100)}%)" for c in (a.get("crops") or [])[:3]
                      if isinstance(c, dict) and isinstance(c.get("confidence"), (int, float)))
    return "\n".join([
        "[APP ANALYSIS] (latest CropSense run)",
        f"Soil type from photo (image model): {a.get('soil_type')} (confidence {a.get('soil_confidence')})",
        f"District reference N/P/K (kg/ha, from published surveys, NOT this field's test): N={a.get('N')}, P={a.get('P')}, K={a.get('K')} ({a.get('npk_district')})",
        f"Weather at analysis time: {a.get('temperature')} °C, humidity {a.get('humidity')} %, rainfall {a.get('rainfall')} mm",
        f"App crop recommendations: {crops or 'n/a'}",
    ])


def knowledge_block(hits: List[dict]) -> str:
    if not hits:
        return "[KNOWLEDGE]\nNo relevant excerpts found in the knowledge base."
    parts = ["[KNOWLEDGE]"]
    for i, h in enumerate(hits, 1):
        parts.append(f"K{i} | {h['title']} › {h['section']}\n{h['text']}")
    return "\n\n".join(parts)


def user_turn(message: str, ui_language: str, profile, location, analysis, hits) -> str:
    return "\n\n".join([
        f"[CONTEXT] App language selected: {config.LANG_NAMES.get(ui_language, 'English')}",
        soil_block(profile, location),
        analysis_block(analysis),
        knowledge_block(hits),
        f"[QUESTION]\n{message}",
    ])
