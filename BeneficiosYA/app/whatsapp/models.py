import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WhatsAppMessage(BaseModel):
    from_number: str
    text: str | None = None
    image_id: str | None = None
    message_type: str = "text"
    message_id: str = ""


def parse_whatsapp_payload(body: dict) -> WhatsAppMessage | None:
    """Extrae el primer mensaje del payload de webhook de Meta. Retorna None si no hay mensaje."""
    try:
        value = body["entry"][0]["changes"][0]["value"]
        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        from_number: str = msg["from"]
        msg_type: str = msg.get("type", "text")
        message_id: str = msg.get("id", "")

        if msg_type == "text":
            return WhatsAppMessage(
                from_number=from_number,
                text=msg.get("text", {}).get("body", ""),
                message_type="text",
                message_id=message_id,
            )

        if msg_type == "image":
            return WhatsAppMessage(
                from_number=from_number,
                image_id=msg.get("image", {}).get("id", ""),
                message_type="image",
                message_id=message_id,
            )

        logger.debug("Tipo de mensaje no soportado: %s", msg_type)
        return None

    except (KeyError, IndexError) as exc:
        logger.warning("Payload de WhatsApp malformado: %s", exc)
        return None
