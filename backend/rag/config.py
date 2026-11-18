"""Configuration for the RAG chatbot (all overridable through environment variables)."""
import os

RAG_DIR = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_DIR = os.getenv("RAG_KB_DIR", os.path.join(RAG_DIR, "knowledge_base"))
INDEX_DIR = os.getenv("RAG_INDEX_DIR", os.path.join(RAG_DIR, "index"))

# Multilingual embeddings so questions in Hindi/Kannada/Tamil/... retrieve English documents.
# E5 models expect "query: " / "passage: " prefixes.
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
QUERY_PREFIX = os.getenv("RAG_QUERY_PREFIX", "query: ")
PASSAGE_PREFIX = os.getenv("RAG_PASSAGE_PREFIX", "passage: ")

CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))

TOP_K = int(os.getenv("RAG_TOP_K", "6"))
MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.72"))   # cosine; E5 scores are compressed (~0.7-0.9)
RELATIVE_WINDOW = float(os.getenv("RAG_RELATIVE_WINDOW", "0.08"))  # keep chunks within this of the best score

# Session memory
SESSION_TTL_S = int(os.getenv("CHAT_SESSION_TTL_S", str(3 * 3600)))
MAX_SESSIONS = int(os.getenv("CHAT_MAX_SESSIONS", "500"))
MAX_HISTORY_TURNS = int(os.getenv("CHAT_MAX_HISTORY_TURNS", "8"))     # user+assistant pairs sent to the LLM

# LLM provider: auto | gemini | anthropic | offline
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))

LANG_CODES = ["en", "hi", "kn", "te", "ta", "ml", "mr", "bn", "gu", "pa", "or"]
LANG_NAMES = {
    "en": "English", "hi": "Hindi", "kn": "Kannada", "te": "Telugu", "ta": "Tamil",
    "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi (Gurmukhi script)", "or": "Odia",
}
