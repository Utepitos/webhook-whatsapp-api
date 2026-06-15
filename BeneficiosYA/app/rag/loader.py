"""
Carga documentos oficiales desde la carpeta /documents.
Soporta .txt, .md y .pdf.

Para agregar documentos:
  1. Coloca los archivos en la carpeta BeneficiosYA/documents/
  2. Reinicia el servidor — se cargan automáticamente al arrancar.

Documentos recomendados:
  - Metodología SISBEN IV (DANE)
  - Decreto de Familias en Acción
  - Resoluciones ICBF
  - Guías de acceso a beneficios
"""

import re
from pathlib import Path
from app.config import settings

try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


def _read_pdf(path: Path) -> str:
    if not HAS_PDF:
        return f"[PDF no procesado: instalar PyPDF2 para leer {path.name}]"
    text = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def load_documents() -> list[dict]:
    """
    Carga todos los documentos de la carpeta de documentos.
    Retorna lista de {source, text, chunks}.
    """
    docs_dir = settings.documents_dir
    if not docs_dir.exists():
        return []

    documents = []
    for path in docs_dir.iterdir():
        if path.suffix.lower() == ".pdf":
            text = _read_pdf(path)
        elif path.suffix.lower() in (".txt", ".md"):
            text = _read_text(path)
        else:
            continue

        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 50:
            continue

        chunks = _chunk_text(text)
        documents.append({"source": path.name, "text": text, "chunks": chunks})
        print(f"[RAG] Cargado: {path.name} ({len(chunks)} fragmentos)")

    return documents
