import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestWebhookVerification:

    def test_verificacion_correcta(self, client):
        with patch("app.whatsapp.webhook.settings") as mock_settings:
            mock_settings.whatsapp_verify_token = "test_token"
            response = client.get("/webhook", params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_token",
                "hub.challenge": "challenge_abc",
            })
        assert response.status_code == 200
        assert response.text == "challenge_abc"

    def test_verificacion_token_incorrecto(self, client):
        with patch("app.whatsapp.webhook.settings") as mock_settings:
            mock_settings.whatsapp_verify_token = "token_correcto"
            response = client.get("/webhook", params={
                "hub.mode": "subscribe",
                "hub.verify_token": "token_incorrecto",
                "hub.challenge": "xyz",
            })
        assert response.status_code == 403

    def test_verificacion_sin_parametros(self, client):
        response = client.get("/webhook")
        assert response.status_code == 403


class TestWebhookMessages:

    def _whatsapp_payload(self, from_number: str, text: str) -> dict:
        return {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": from_number,
                            "type": "text",
                            "id": "msg_001",
                            "text": {"body": text}
                        }]
                    }
                }]
            }]
        }

    def test_mensaje_texto_retorna_200(self, client):
        payload = self._whatsapp_payload("573001234567", "Hola, necesito ayuda")
        with patch("app.whatsapp.webhook.process_message", new_callable=AsyncMock) as mock_process, \
             patch("app.whatsapp.webhook.send_text_message", new_callable=AsyncMock) as mock_send:
            mock_process.return_value = "Hola, bienvenido a BeneficiosYA"
            mock_send.return_value = True
            response = client.post("/webhook", json=payload)
        assert response.status_code == 200

    def test_payload_vacio_retorna_200(self, client):
        response = client.post("/webhook", json={})
        assert response.status_code == 200

    def test_payload_sin_mensajes_retorna_200(self, client):
        response = client.post("/webhook", json={"entry": [{"changes": [{"value": {}}]}]})
        assert response.status_code == 200


class TestChatAPI:

    def test_chat_endpoint_existe(self, client):
        with patch("app.agent.chatbot.process_message", new_callable=AsyncMock) as mock:
            mock.return_value = "Respuesta de prueba"
            response = client.post("/chat", json={
                "session_id": "test_user_001",
                "message": "Hola, tengo 3 hijos y vivo en Bogotá"
            })
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "session_id" in data

    def test_reset_sesion(self, client):
        response = client.delete("/chat/test_user_reset")
        assert response.status_code == 200

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
