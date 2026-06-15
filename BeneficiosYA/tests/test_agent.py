import pytest
from unittest.mock import patch, AsyncMock
from app.agent.session import Session, UserProfile, get_session, delete_session
from app.agent.chatbot import process_message, _build_context, _refresh_profile_insights


class TestSession:

    def test_crear_sesion_nueva(self):
        session = get_session("user_nuevo_999")
        assert session.user_id == "user_nuevo_999"
        assert session.history == []
        assert session.sisben_aproximado is None

    def test_agregar_mensaje_a_historial(self):
        session = Session(user_id="test")
        session.add_message("user", "Hola")
        session.add_message("assistant", "Bienvenido")
        assert len(session.history) == 2
        assert session.history[0]["role"] == "user"

    def test_get_recent_history_limita_mensajes(self):
        session = Session(user_id="test")
        for i in range(20):
            session.add_message("user", f"Mensaje {i}")
        recent = session.get_recent_history(n=5)
        assert len(recent) == 5

    def test_eliminar_sesion(self):
        get_session("user_a_eliminar")
        delete_session("user_a_eliminar")
        nueva = get_session("user_a_eliminar")
        assert nueva.history == []

    def test_sesion_persistente_entre_llamadas(self):
        session1 = get_session("user_persistente")
        session1.sisben_aproximado = "B"
        session2 = get_session("user_persistente")
        assert session2.sisben_aproximado == "B"
        delete_session("user_persistente")


class TestUpdateProfile:

    def test_calcula_sisben_con_tres_campos(self):
        session = Session(user_id="test_profile")
        session.profile.material_piso = "tierra"
        session.profile.situacion_laboral = "desempleado"
        session.profile.num_personas_hogar = 5
        _refresh_profile_insights(session)
        assert session.sisben_aproximado in ("A", "B", "C", "D")

    def test_no_recalcula_sisben_si_ya_existe(self):
        session = Session(user_id="test_no_recalc")
        session.sisben_aproximado = "A"
        session.profile.material_piso = "tierra"
        session.profile.situacion_laboral = "desempleado"
        session.profile.num_personas_hogar = 5
        _refresh_profile_insights(session)
        assert session.sisben_aproximado == "A"  # No debe cambiar

    def test_no_calcula_con_menos_de_tres_campos(self):
        session = Session(user_id="test_pocos_datos")
        session.profile.edad = 30
        _refresh_profile_insights(session)
        assert session.sisben_aproximado is None


class TestChatbot:

    @pytest.mark.asyncio
    async def test_process_message_sin_claude_retorna_fallback(self):
        session = Session(user_id="test_no_claude")
        with patch("app.agent.chatbot.settings") as mock_settings:
            mock_settings.has_claude = False
            reply = await process_message(session, "Hola")
        assert len(reply) > 0

    @pytest.mark.asyncio
    async def test_process_message_con_claude_mock(self):
        session = Session(user_id="test_con_claude")

        mock_response = type("Response", (), {
            "content": [type("Block", (), {"text": "Hola, bienvenido a BeneficiosYA"})()]
        })()

        with patch("app.agent.chatbot.settings") as mock_settings, \
             patch("anthropic.Anthropic") as mock_anthropic:
            mock_settings.has_claude = True
            mock_settings.anthropic_api_key = "fake_key"
            mock_client = mock_anthropic.return_value
            mock_client.messages.create.return_value = mock_response

            reply = await process_message(session, "Necesito ayuda")

        assert "bienvenido" in reply.lower() or len(reply) > 0
        assert len(session.history) == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_mensaje_agrega_al_historial(self):
        session = Session(user_id="test_historial")
        with patch("app.agent.chatbot.settings") as mock_settings:
            mock_settings.has_claude = False
            await process_message(session, "Tengo 3 hijos")
        assert any(m["content"] == "Tengo 3 hijos" for m in session.history)

    def test_build_context_con_perfil_completo(self):
        session = Session(user_id="test_context")
        session.profile.edad = 35
        session.profile.situacion_laboral = "informal"
        session.sisben_aproximado = "B"
        session.beneficios_identificados = ["familias_en_accion", "regimen_subsidiado_salud"]

        with patch("app.agent.chatbot.retrieve", return_value=""):
            context = _build_context(session, "¿Qué beneficios tengo?")

        assert "35" in context
        assert "B" in context

    def test_build_context_vacio_sin_datos(self):
        session = Session(user_id="test_context_vacio")
        with patch("app.agent.chatbot.retrieve", return_value=""):
            context = _build_context(session, "Hola")
        assert context == ""
