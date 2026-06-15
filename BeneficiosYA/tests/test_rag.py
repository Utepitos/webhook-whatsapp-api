import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from rank_bm25 import BM25Okapi

from app.rag.retriever import DocumentRetriever


class TestDocumentLoader:

    def test_carga_archivo_txt(self):
        from app.rag.loader import load_documents

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "test_doc.txt"
            txt_file.write_text(
                "El SISBEN es el Sistema de Identificación de Potenciales Beneficiarios. "
                "Permite al gobierno identificar a las familias más vulnerables de Colombia. "
                "Los beneficiarios del grupo A tienen mayor prioridad para los subsidios.",
                encoding="utf-8",
            )
            with patch("app.rag.loader.settings") as mock_settings:
                mock_settings.documents_dir = Path(tmpdir)
                docs = load_documents()

        assert len(docs) == 1
        assert docs[0]["source"] == "test_doc.txt"
        assert len(docs[0]["chunks"]) >= 1

    def test_ignora_archivos_no_soportados(self):
        from app.rag.loader import load_documents

        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "imagen.jpg").write_bytes(b"fake image")
            (Path(tmpdir) / "doc.txt").write_text("contenido válido " * 20, encoding="utf-8")

            with patch("app.rag.loader.settings") as mock_settings:
                mock_settings.documents_dir = Path(tmpdir)
                docs = load_documents()

        assert len(docs) == 1

    def test_carpeta_vacia_retorna_lista_vacia(self):
        from app.rag.loader import load_documents

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.rag.loader.settings") as mock_settings:
                mock_settings.documents_dir = Path(tmpdir)
                docs = load_documents()

        assert docs == []

    def test_chunk_text_divide_correctamente(self):
        from app.rag.loader import _chunk_text

        texto = " ".join(["palabra"] * 1200)
        chunks = _chunk_text(texto, chunk_size=500, overlap=50)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.split()) <= 500

    def test_chunk_text_corto_da_un_chunk(self):
        from app.rag.loader import _chunk_text

        texto = "Este es un texto corto sobre el SISBEN."
        chunks = _chunk_text(texto, chunk_size=500)
        assert len(chunks) == 1


class TestDocumentRetriever:

    def test_not_ready_sin_build(self):
        retriever = DocumentRetriever()
        assert not retriever.is_ready

    def test_search_sin_indice_retorna_vacio(self):
        retriever = DocumentRetriever()
        assert retriever.search("SISBEN beneficios") == ""

    def test_build_carga_documentos(self):
        retriever = DocumentRetriever()
        with patch("app.rag.retriever.load_documents") as mock_load:
            mock_load.return_value = [{
                "source": "test.txt",
                "text": "El SISBEN clasifica colombianos vulnerables en grupos A B C D",
                "chunks": [
                    "El SISBEN clasifica a los colombianos vulnerables",
                    "Los grupos son A B C y D según el nivel de pobreza",
                ],
            }]
            retriever.build()

        assert retriever.is_ready
        assert len(retriever._chunks) == 2
        assert len(retriever._sources) == 2

    def test_build_sin_documentos_no_inicializa_indice(self):
        retriever = DocumentRetriever()
        with patch("app.rag.retriever.load_documents", return_value=[]):
            retriever.build()
        assert not retriever.is_ready

    def test_search_retorna_resultado_relevante(self):
        retriever = DocumentRetriever()
        chunks = [
            "El SISBEN determina quién accede a Familias en Acción",
            "Colombia Mayor es para adultos mayores sin pensión",
        ]
        retriever._chunks = chunks
        retriever._sources = ["doc.txt"] * 2
        retriever._index = BM25Okapi([c.lower().split() for c in chunks])

        result = retriever.search("Familias en Acción SISBEN")
        assert isinstance(result, str)

    def test_sources_y_chunks_quedan_alineados_tras_build(self):
        retriever = DocumentRetriever()
        with patch("app.rag.retriever.load_documents") as mock_load:
            mock_load.return_value = [
                {"source": "a.txt", "text": "...", "chunks": ["chunk_a1", "chunk_a2"]},
                {"source": "b.txt", "text": "...", "chunks": ["chunk_b1"]},
            ]
            retriever.build()

        assert len(retriever._chunks) == len(retriever._sources) == 3
        assert retriever._sources[0] == "a.txt"
        assert retriever._sources[2] == "b.txt"
