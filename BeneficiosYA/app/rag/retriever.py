"""
Motor de recuperación de información usando BM25.
Si no hay documentos cargados, devuelve contexto vacío.
"""

from rank_bm25 import BM25Okapi
from app.rag.loader import load_documents

_index: BM25Okapi | None = None
_chunks: list[str] = []
_sources: list[str] = []


def build_index() -> None:
    """Construye el índice BM25 a partir de los documentos cargados."""
    global _index, _chunks, _sources

    documents = load_documents()
    if not documents:
        print("[RAG] Sin documentos en /documents. El agente usará solo su conocimiento base.")
        return

    for doc in documents:
        for chunk in doc["chunks"]:
            _chunks.append(chunk)
            _sources.append(doc["source"])

    tokenized = [c.lower().split() for c in _chunks]
    _index = BM25Okapi(tokenized)
    print(f"[RAG] Índice construido: {len(_chunks)} fragmentos de {len(documents)} documento(s)")


def retrieve(query: str, top_k: int = 4) -> str:
    """Recupera los fragmentos más relevantes para una consulta."""
    if _index is None or not _chunks:
        return ""

    tokens = query.lower().split()
    scores = _index.get_scores(tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    seen_sources = set()
    for idx in top_indices:
        if scores[idx] < 0.1:
            continue
        source = _sources[idx]
        results.append(f"[Fuente: {source}]\n{_chunks[idx]}")
        seen_sources.add(source)

    if not results:
        return ""

    return "\n\n---\n".join(results)
