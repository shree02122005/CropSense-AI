"""Semantic retrieval over the agricultural knowledge base."""
from typing import Dict, List, Optional

from . import config
from .ingest import get_store


def _cosine_from_l2(d: float) -> float:
    # Embeddings are L2-normalised, FAISS IndexFlatL2 returns squared L2: |a-b|^2 = 2 - 2cos.
    return 1.0 - float(d) / 2.0


def search(query: str, k: int = config.TOP_K) -> List[dict]:
    store = get_store()
    hits = store.similarity_search_with_score(query, k=k)
    return [{
        "id": doc.metadata.get("chunk_id"),
        "title": doc.metadata.get("title"),
        "section": doc.metadata.get("section"),
        "source": doc.metadata.get("source"),
        "text": doc.page_content,
        "score": round(_cosine_from_l2(dist), 4),
    } for doc, dist in hits]


def build_queries(message: str, soil_profile: Optional[dict], analysis: Optional[dict],
                  history: List[dict], last_crops: List[str]) -> List[str]:
    """
    Query understanding for retrieval:
      q1 = the user's message as asked (any language)
      q2 = the message enriched with known soil facts and conversation focus, so short
           follow-ups ("why this crop?", "what fertilizer?") still retrieve the right documents.
    """
    facts = []
    if soil_profile and soil_profile.get("status") in ("ok", "partial"):
        der = soil_profile.get("derived", {})
        if der.get("texture_class_0_30cm"):
            facts.append(f"{der['texture_class_0_30cm']} soil texture")
        if der.get("ph_class_0_30cm"):
            ph = soil_profile.get("summary_0_30cm", {}).get("phh2o")
            facts.append(f"{der['ph_class_0_30cm']} soil pH {ph:.1f}" if ph else f"{der['ph_class_0_30cm']} soil")
        if der.get("organic_carbon_class"):
            facts.append(f"{der['organic_carbon_class']} organic carbon")
        for flag in der.get("screening_flags", [])[:2]:
            facts.append(flag["flag"])
    if analysis and analysis.get("soil_type"):
        facts.append(f"{analysis['soil_type']} soil")
    prev_user = next((h["content"] for h in reversed(history) if h["role"] == "user"), "")
    focus = []
    if last_crops:
        focus.append("crops discussed: " + ", ".join(last_crops[:4]))
    if prev_user and len(message.split()) < 12:
        focus.append("previous question: " + prev_user[:200])
    q2 = " ; ".join([message] + facts + focus)
    return [message] if q2 == message else [message, q2]


def retrieve(message: str, soil_profile: Optional[dict] = None, analysis: Optional[dict] = None,
             history: Optional[List[dict]] = None, last_crops: Optional[List[str]] = None,
             k: int = config.TOP_K) -> List[dict]:
    """Merge results of both queries, keep the most relevant chunks above the similarity floor."""
    merged: Dict[str, dict] = {}
    for q in build_queries(message, soil_profile, analysis, history or [], last_crops or []):
        for hit in search(q, k=k):
            if hit["id"] not in merged or hit["score"] > merged[hit["id"]]["score"]:
                merged[hit["id"]] = hit
    hits = sorted(merged.values(), key=lambda h: h["score"], reverse=True)
    if not hits:
        return []
    best = hits[0]["score"]
    kept = [h for h in hits if h["score"] >= config.MIN_SIMILARITY and h["score"] >= best - config.RELATIVE_WINDOW]
    return kept[:k]
