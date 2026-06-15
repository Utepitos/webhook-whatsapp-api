import httpx
import base64
from app.config import settings


GRAPH_URL = "https://graph.facebook.com/v19.0"


async def send_text_message(to: str, text: str) -> bool:
    if not settings.has_whatsapp:
        print(f"[WhatsApp DEMO] → {to}: {text[:100]}...")
        return True

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_URL}/{settings.whatsapp_phone_id}/messages",
            headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text},
            },
            timeout=10.0,
        )
        return resp.status_code == 200


async def send_typing_indicator(to: str) -> None:
    """Marca el chat como 'escribiendo...' mientras el agente procesa."""
    if not settings.has_whatsapp:
        return

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{GRAPH_URL}/{settings.whatsapp_phone_id}/messages",
            headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
            json={
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": "typing",
            },
            timeout=5.0,
        )


async def download_image_as_base64(media_id: str) -> str | None:
    """Descarga una imagen de WhatsApp y la devuelve en base64."""
    if not settings.has_whatsapp:
        return None

    async with httpx.AsyncClient() as client:
        # Paso 1: obtener URL de la imagen
        resp = await client.get(
            f"{GRAPH_URL}/{media_id}",
            headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None

        media_url = resp.json().get("url")
        if not media_url:
            return None

        # Paso 2: descargar la imagen
        img_resp = await client.get(
            media_url,
            headers={"Authorization": f"Bearer {settings.whatsapp_token}"},
            timeout=20.0,
        )
        if img_resp.status_code != 200:
            return None

        return base64.b64encode(img_resp.content).decode("utf-8")
