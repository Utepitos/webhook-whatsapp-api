from fastapi import APIRouter, Request, Response
from app.config import settings
from app.whatsapp.models import parse_whatsapp_payload
from app.whatsapp.client import send_text_message, download_image_as_base64
from app.agent.session import get_session
from app.agent.chatbot import process_message, process_image_message

router = APIRouter()


@router.get("")
async def verify_webhook(request: Request):
    """Verificación del webhook con Meta."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)


@router.post("")
async def receive_message(request: Request):
    """Recibe y procesa mensajes entrantes de WhatsApp."""
    body = await request.json()

    # Siempre responder 200 a Meta (evita reenvíos)
    incoming = parse_whatsapp_payload(body)
    if not incoming:
        return Response(status_code=200)

    user_id = incoming.from_number
    session = get_session(user_id)

    try:
        if incoming.message_type == "image" and incoming.image_id:
            image_b64 = await download_image_as_base64(incoming.image_id)
            if image_b64:
                reply = await process_image_message(session, image_b64, incoming.text or "")
            else:
                reply = await process_message(session, "El usuario compartió una foto de su vivienda pero no pude descargarla.")
        else:
            reply = await process_message(session, incoming.text or "")

        await send_text_message(user_id, reply)
    except Exception as e:
        print(f"[Error] {user_id}: {e}")
        await send_text_message(user_id, "Lo siento, hubo un problema. Por favor intenta de nuevo en un momento.")

    return Response(status_code=200)
