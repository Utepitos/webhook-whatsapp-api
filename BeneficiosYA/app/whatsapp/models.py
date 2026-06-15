from pydantic import BaseModel
from typing import Any


class WhatsAppMessage(BaseModel):
    from_number: str
    text: str | None = None
    image_id: str | None = None
    message_type: str = "text"
    message_id: str = ""


def parse_whatsapp_payload(body: dict) -> WhatsAppMessage | None:
    try:
        entry = body.get("entry", [{}])[0]
        change = entry.get("changes", [{}])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        msg = messages[0]
        from_number = msg.get("from", "")
        msg_type = msg.get("type", "text")
        message_id = msg.get("id", "")

        if msg_type == "text":
            return WhatsAppMessage(
                from_number=from_number,
                text=msg.get("text", {}).get("body", ""),
                message_type="text",
                message_id=message_id,
            )
        elif msg_type == "image":
            return WhatsAppMessage(
                from_number=from_number,
                image_id=msg.get("image", {}).get("id", ""),
                message_type="image",
                message_id=message_id,
            )
        return None
    except Exception:
        return None
