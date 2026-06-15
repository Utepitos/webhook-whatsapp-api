"""Motor de recuperación BM25 sobre documentos oficiales."""

from rank_bm25 import BM25Okapi
from app.rag.loader import load_documents
from app.constants import RAG_TOP_K, RAG_MIN_SCORE


class DocumentRetriever:
    """Encapsula el índice BM25 y la búsqueda sobre documentos cargados."""

    def __init__(self) -> None:
        self._index: BM25Okapi | None = None
        self._chunks: list[str] = []
        self._sources: list[str] = []

    @property
    def is_ready(self) -> bool:
        return self._index is not None and bool(self._chunks)

    def build(self) -> None:
        """Construye el índice a partir de los documentos en /documents."""
        documents = load_documents()
        if not documents:
            print("[RAG] Sin documentos en /documents. El agente usará solo su conocimiento base.")
            return

        self._chunks = [chunk for doc in documents for chunk in doc["chunks"]]
        self._sources = [doc["source"] for doc in documents for _ in doc["chunks"]]

        self._index = BM25Okapi([c.lower().split() for c in self._chunks])
        print(f"[RAG] Índice construido: {len(self._chunks)} fragmentos de {len(documents)} documento(s)")

    def search(self, query: str, top_k: int = RAG_TOP_K) -> str:
        """Retorna los fragmentos más relevantes para una consulta."""
        if not self.is_ready:
            return ""

        scores = self._index.get_scores(query.lower().split())  # type: ignore[union-attr]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        results = [
            f"[Fuente: {self._sources[i]}]\n{self._chunks[i]}"
            for i in ranked[:top_k]
            if scores[i] >= RAG_MIN_SCORE
        ]
        return "\n\n---\n".join(results)


# Singleton de la aplicación
_retriever = DocumentRetriever()


def build_index() -> None:
    _retriever.build()


def retrieve(query: str) -> str:
    return _retriever.search(query)
