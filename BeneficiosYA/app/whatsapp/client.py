import base64
import logging
import httpx
from app.config import settings
from app.constants import WHATSAPP_API_URL, WHATSAPP_REQUEST_TIMEOUT, WHATSAPP_IMAGE_DOWNLOAD_TIMEOUT

logger = logging.getLogger(__name__)

_AUTH_HEADER_TEMPLATE = "Bearer {}"
_WHATSAPP_PRODUCT = "whatsapp"


def _auth_headers() -> dict[str, str]:
    return {"Authorization": _AUTH_HEADER_TEMPLATE.format(settings.whatsapp_token)}


def _messages_url() -> str:
    return f"{WHATSAPP_API_URL}/{settings.whatsapp_phone_id}/messages"


async def send_text_message(to: str, text: str) -> bool:
    if not settings.has_whatsapp:
        logger.info("[WhatsApp DEMO] → %s: %s...", to, text[:100])
        return True

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _messages_url(),
            headers=_auth_headers(),
            json={
                "messaging_product": _WHATSAPP_PRODUCT,
                "to": to,
                "type": "text",
                "text": {"body": text},
            },
            timeout=WHATSAPP_REQUEST_TIMEOUT,
        )
        if not resp.is_success:
            logger.error("Error enviando mensaje a %s: %s %s", to, resp.status_code, resp.text)
        return resp.is_success


async def send_typing_indicator(to: str) -> None:
    """Marca el chat como 'escribiendo...' mientras el agente procesa."""
    if not settings.has_whatsapp:
        return

    async with httpx.AsyncClient() as client:
        await client.post(
            _messages_url(),
            headers=_auth_headers(),
            json={
                "messaging_product": _WHATSAPP_PRODUCT,
                "status": "read",
                "message_id": to,
            },
            timeout=WHATSAPP_REQUEST_TIMEOUT,
        )


async def download_image_as_base64(media_id: str) -> str | None:
    """Descarga una imagen de WhatsApp y la retorna en base64."""
    if not settings.has_whatsapp:
        return None

    async with httpx.AsyncClient() as client:
        media_resp = await client.get(
            f"{WHATSAPP_API_URL}/{media_id}",
            headers=_auth_headers(),
            timeout=WHATSAPP_REQUEST_TIMEOUT,
        )
        if not media_resp.is_success:
            logger.error("No se pudo obtener URL de media %s: %s", media_id, media_resp.status_code)
            return None

        media_url: str | None = media_resp.json().get("url")
        if not media_url:
            logger.error("URL de media vacía para media_id %s", media_id)
            return None

        image_resp = await client.get(
            media_url,
            headers=_auth_headers(),
            timeout=WHATSAPP_IMAGE_DOWNLOAD_TIMEOUT,
        )
        if not image_resp.is_success:
            logger.error("No se pudo descargar imagen de %s: %s", media_url, image_resp.status_code)
            return None

        return base64.b64encode(image_resp.content).decode("utf-8")
