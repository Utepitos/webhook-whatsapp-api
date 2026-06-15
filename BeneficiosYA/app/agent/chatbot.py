import json
import anthropic
from app.config import settings
from app.agent.session import Session
from app.agent.sisben import aproximar_grupo_sisben
from app.agent.benefits import match_benefits
from app.rag.retriever import retrieve
from app.constants import CLAUDE_MODEL, MAX_TOKENS_CHAT, MAX_HISTORY_MESSAGES, MIN_PROFILE_FIELDS_FOR_SISBEN
from app.vision.analyzer import analyze_house_image

_SYSTEM_PROMPT = """Eres *BeneficiosYA*, un asistente social virtual del gobierno colombiano. Eres empático, paciente y hablas en lenguaje sencillo, usando el tuteo colombiano.

TU MISIÓN:
Ayudar a ciudadanos colombianos en situación de vulnerabilidad a conocer y acceder a los beneficios y programas del Estado que les corresponden: subsidios, salud gratuita, educación, vivienda, alimentación y más.

CÓMO TRABAJAS:
• Escuchas activamente la situación de la persona sin juzgar
• Haces preguntas naturales y conversacionales para entender su perfil (NUNCA hagas todas las preguntas de una vez)
• Una vez tengas suficiente información, identifies los beneficios que aplican para su caso específico
• Explicas paso a paso cómo acceder a cada beneficio
• Si el usuario comparte una foto de su vivienda, la tienes en cuenta para complementar tu análisis

INFORMACIÓN QUE NECESITAS RECOPILAR (naturalmente, en el orden que fluya la conversación):
- Edad y si es hombre o mujer
- Municipio y departamento donde vive
- Composición del hogar: quiénes viven ahí, edades aproximadas
- Si es mujer cabeza de hogar (sola al frente del hogar)
- Situación laboral: trabaja, qué tipo de trabajo, ingresos aproximados
- Condiciones de vivienda: de qué material son las paredes, techo, piso
- Si tienen servicios: agua potable, luz, alcantarillado
- Si tienen vivienda propia, arrendada, prestada o en invasión
- Si hay menores en edad escolar
- Si hay adultos mayores (57+ mujeres, 62+ hombres)
- Si algún miembro tiene discapacidad
- Si son víctimas del conflicto armado o desplazados
- Si ya tienen SISBEN y qué grupo

ESTILO DE COMUNICACIÓN:
• Usa lenguaje simple, cálido y cercano
• Válida los sentimientos: "Entiendo que es difícil..."
• Sé específico: nombres reales de programas, montos reales, pasos concretos
• Divide la información en partes digeribles
• Termina con un mensaje alentador
• Cuando des beneficios, ordénalos por impacto/urgencia

IMPORTANTE:
• Basas tus respuestas en los documentos oficiales y la información que te proporciono
• Siempre aclara que es orientación y que deben verificar con las entidades oficiales
• No inventes montos o requisitos que no tienes seguros
• Si el usuario pregunta algo que no sabes, dilo honestamente y sugiere a dónde acudir
"""

_NO_API_KEY_GREETING = """¡Hola! Soy *BeneficiosYA* 🇨🇴

Estoy aquí para ayudarte a conocer los beneficios y programas del gobierno colombiano a los que puedes acceder.

Cuéntame un poco sobre tu situación: ¿cómo está tu familia? ¿Cuántas personas viven en tu hogar y cuántos años tienes?

También puedes compartirme una foto de tu vivienda si quieres que te ayude a evaluar mejor tu situación."""

_NO_API_KEY_FOLLOWUP = (
    "Para darte una orientación personalizada necesito la API key de Claude. "
    "Por favor revisa el archivo .env y agrega tu ANTHROPIC_API_KEY."
)


def _build_context(session: Session, user_message: str) -> str:
    """Reúne perfil acumulado, SISBEN estimado y fragmentos RAG relevantes."""
    parts: list[str] = []

    profile_data = {k: v for k, v in vars(session.profile).items() if v is not None}
    if profile_data:
        parts.append(f"PERFIL ACTUAL DEL USUARIO:\n{json.dumps(profile_data, ensure_ascii=False, indent=2)}")

    if session.sisben_aproximado:
        parts.append(f"SISBEN APROXIMADO: Grupo {session.sisben_aproximado}")

    if session.beneficios_identificados:
        parts.append(f"BENEFICIOS PREVIAMENTE IDENTIFICADOS: {', '.join(session.beneficios_identificados)}")

    if session.profile.analisis_imagen:
        parts.append(f"ANÁLISIS DE IMAGEN DE VIVIENDA:\n{session.profile.analisis_imagen}")

    rag_context = retrieve(user_message)
    if rag_context:
        parts.append(f"DOCUMENTOS DE REFERENCIA OFICIAL:\n{rag_context}")

    return "\n\n".join(parts)


def _refresh_profile_insights(session: Session) -> None:
    """Recalcula el grupo SISBEN y beneficios elegibles cuando hay datos suficientes."""
    if session.sisben_aproximado:
        return

    profile = session.profile
    relevant_fields = [
        profile.edad, profile.situacion_laboral, profile.ingreso_mensual_aprox,
        profile.material_piso, profile.acceso_agua_potable, profile.tenencia_vivienda,
        profile.es_mujer_cabeza_hogar, profile.num_personas_hogar,
    ]
    filled_count = sum(1 for v in relevant_fields if v is not None)

    if filled_count < MIN_PROFILE_FIELDS_FOR_SISBEN:
        return

    grupo, _ = aproximar_grupo_sisben(profile)
    session.sisben_aproximado = grupo
    session.beneficios_identificados = [b["id"] for b in match_benefits(profile, grupo)]


def _reply_without_claude(session: Session) -> str:
    is_first_message = len(session.history) <= 1
    return _NO_API_KEY_GREETING if is_first_message else _NO_API_KEY_FOLLOWUP


async def _call_claude(session: Session, user_message: str) -> str:
    context = _build_context(session, user_message)
    history = session.get_recent_history(n=MAX_HISTORY_MESSAGES)

    if context:
        history = history[:-1] + [{
            "role": "user",
            "content": f"{context}\n\nMENSAJE DEL USUARIO: {user_message}",
        }]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS_CHAT,
        system=_SYSTEM_PROMPT,
        messages=history,
    )
    return response.content[0].text


async def process_message(session: Session, user_message: str) -> str:
    """Procesa un mensaje de texto y retorna la respuesta del agente."""
    session.add_message("user", user_message)
    _refresh_profile_insights(session)

    if not settings.has_claude:
        reply = _reply_without_claude(session)
        session.add_message("assistant", reply)
        return reply

    reply = await _call_claude(session, user_message)
    session.add_message("assistant", reply)
    return reply


async def process_image_message(session: Session, image_base64: str, caption: str = "") -> str:
    """Analiza la imagen de la vivienda y la incorpora al contexto de la conversación."""
    analysis = await analyze_house_image(image_base64)
    session.profile.imagen_vivienda_analizada = True
    session.profile.analisis_imagen = analysis

    user_message = (
        f"{caption}\n\n[ANÁLISIS AUTOMÁTICO DE LA IMAGEN]:\n{analysis}"
        if caption
        else f"El usuario compartió una foto de su vivienda.\n\n[ANÁLISIS]:\n{analysis}"
    )
    return await process_message(session, user_message)
