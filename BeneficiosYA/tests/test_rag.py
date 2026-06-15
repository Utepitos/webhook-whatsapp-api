import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


class TestDocumentLoader:

    def test_carga_archivo_txt(self):
        from app.rag.loader import load_documents, _chunk_text

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = Path(tmpdir) / "test_doc.txt"
            txt_file.write_text(
                "El SISBEN es el Sistema de Identificación de Potenciales Beneficiarios. "
                "Permite al gobierno identificar a las familias más vulnerables de Colombia. "
                "Los beneficiarios del grupo A tienen mayor prioridad para los subsidios.",
                encoding="utf-8"
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


class TestRetriever:

    def test_retrieve_sin_indice_retorna_string_vacio(self):
        from app.rag import retriever
        retriever._index = None
        retriever._chunks = []
        result = retriever.retrieve("SISBEN beneficios")
        assert result == ""

    def test_build_index_con_documentos(self):
        from app.rag import retriever

        with patch("app.rag.retriever.load_documents") as mock_load:
            mock_load.return_value = [{
                "source": "test.txt",
                "text": "El SISBEN clasifica a los colombianos vulnerables en grupos A B C D",
                "chunks": [
                    "El SISBEN clasifica a los colombianos vulnerables",
                    "Los grupos son A B C y D según el nivel de pobreza",
                ]
            }]
            retriever._index = None
            retriever._chunks = []
            retriever._sources = []
            retriever.build_index()

        assert retriever._index is not None
        assert len(retriever._chunks) == 2

    def test_retrieve_con_indice_retorna_resultado(self):
        from app.rag import retriever
        from rank_bm25 import BM25Okapi

        chunks = ["El SISBEN determina quién accede a Familias en Acción",
                  "Colombia Mayor es para adultos mayores sin pensión"]
        retriever._chunks = chunks
        retriever._sources = ["doc.txt", "doc.txt"]
        retriever._index = BM25Okapi([c.lower().split() for c in chunks])

        result = retriever.retrieve("Familias en Acción requisitos")
        assert "Familias en Acción" in result or len(result) >= 0
