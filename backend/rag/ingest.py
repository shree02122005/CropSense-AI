"""
Knowledge-base ingestion:  load documents -> chunk -> embed -> FAISS vector store.

The index is persisted in backend/rag/index/ together with a manifest (embedding
model + hash of the documents + chunk settings). It is rebuilt automatically when
any document or setting changes.

    python -m backend.rag.ingest            # build / refresh the index manually
"""
import glob
import hashlib
import json
import os
import re
import threading
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from . import config

_lock = threading.Lock()
_store = None
_embeddings = None


# ── 1. Document loading ──────────────────────────────────────────────────────
def _parse_front_matter(text: str) -> Tuple[dict, str]:
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def load_documents(kb_dir: str = config.KNOWLEDGE_BASE_DIR) -> List[Document]:
    docs = []
    for path in sorted(glob.glob(os.path.join(kb_dir, "*.md")) + glob.glob(os.path.join(kb_dir, "*.txt"))):
        with open(path, encoding="utf-8") as f:
            meta, body = _parse_front_matter(f.read())
        name = os.path.basename(path)
        docs.append(Document(page_content=body, metadata={
            "source": name,
            "title": meta.get("title", os.path.splitext(name)[0]),
            "topic": meta.get("topic", ""),
            "basis": meta.get("basis", ""),
        }))
    return docs


# ── 2. Chunking ──────────────────────────────────────────────────────────────
def chunk_documents(docs: List[Document]) -> List[Document]:
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "h1"), ("##", "section")], strip_headers=False)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP,
                                                   separators=["\n\n", "\n", ". ", " ", ""])
    chunks = []
    for doc in docs:
        for sec in header_splitter.split_text(doc.page_content):
            section = sec.metadata.get("section") or sec.metadata.get("h1") or doc.metadata["title"]
            for i, piece in enumerate(text_splitter.split_text(sec.page_content)):
                # Prefix the document title so each chunk is self-describing for retrieval.
                content = f"{doc.metadata['title']} — {section}\n{piece.strip()}"
                chunks.append(Document(page_content=content, metadata={
                    **doc.metadata, "section": section,
                    "chunk_id": f"{os.path.splitext(doc.metadata['source'])[0]}#{len(chunks)}",
                }))
    return chunks


# ── 3. Embeddings ────────────────────────────────────────────────────────────
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "prompt": config.PASSAGE_PREFIX},
            query_encode_kwargs={"normalize_embeddings": True, "prompt": config.QUERY_PREFIX},
        )
    return _embeddings


# ── 4. Vector store (FAISS, persisted) ───────────────────────────────────────
def _manifest(docs: List[Document]) -> dict:
    h = hashlib.sha256()
    for d in docs:
        h.update(d.metadata["source"].encode()); h.update(d.page_content.encode())
    return {"embedding_model": config.EMBEDDING_MODEL, "passage_prefix": config.PASSAGE_PREFIX,
            "chunk_size": config.CHUNK_SIZE, "chunk_overlap": config.CHUNK_OVERLAP, "kb_sha256": h.hexdigest()}


def build_index(force: bool = False):
    """Load the persisted index if it matches the knowledge base, otherwise (re)build it."""
    from langchain_community.vectorstores import FAISS

    docs = load_documents()
    if not docs:
        raise RuntimeError(f"No knowledge-base documents found in {config.KNOWLEDGE_BASE_DIR}")
    manifest = _manifest(docs)
    manifest_path = os.path.join(config.INDEX_DIR, "manifest.json")
    emb = get_embeddings()

    if not force and os.path.exists(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                saved = json.load(f)
            if {k: saved.get(k) for k in manifest} == manifest:
                # Our own index files, written by build_index below.
                return FAISS.load_local(config.INDEX_DIR, emb, allow_dangerous_deserialization=True), saved
        except (OSError, ValueError):
            pass

    chunks = chunk_documents(docs)
    store = FAISS.from_documents(chunks, emb)
    os.makedirs(config.INDEX_DIR, exist_ok=True)
    store.save_local(config.INDEX_DIR)
    manifest.update({"documents": len(docs), "chunks": len(chunks)})
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return store, manifest


def get_store():
    """Thread-safe lazy singleton."""
    global _store
    if _store is None:
        with _lock:
            if _store is None:
                _store, _ = build_index()
    return _store


def is_ready() -> bool:
    return _store is not None


def warm_up_in_background():
    threading.Thread(target=lambda: _safe(get_store), daemon=True, name="rag-warmup").start()


def _safe(fn):
    try:
        fn()
    except Exception as e:  # logged; requests will retry lazily
        print(f"[rag] index warm-up failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    store, manifest = build_index(force=True)
    print(json.dumps(manifest, indent=2))
