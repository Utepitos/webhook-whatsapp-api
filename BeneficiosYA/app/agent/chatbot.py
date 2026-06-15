import json
import anthropic
from app.config import settings
from app.agent.session import Session, UserProfile
from app.agent.sisben import aproximar_grupo_sisben
from app.agent.benefits import match_benefits, format_benefits_summary
from app.rag.retriever import retrieve

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

_FALLBACK_RESPONSE = """¡Hola! Soy *BeneficiosYA* 🇨🇴

Estoy aquí para ayudarte a conocer los beneficios y programas del gobierno colombiano a los que puedes acceder.

Cuéntame un poco sobre tu situación: ¿cómo está tu familia? ¿Cuántas personas viven en tu hogar y cuántos años tienes?

También puedes compartirme una foto de tu vivienda si quieres que te ayude a evaluar mejor tu situación."""


def _build_context(session: Session, user_message: str) -> str:
    """Construye el contexto adicional para el agente."""
    parts = []

    # Perfil acumulado
    profile_dict = {k: v for k, v in vars(session.profile).items() if v is not None}
    if profile_dict:
        parts.append(f"PERFIL ACTUAL DEL USUARIO:\n{json.dumps(profile_dict, ensure_ascii=False, indent=2)}")

    # SISBEN aproximado si ya hay datos suficientes
    if session.sisben_aproximado:
        parts.append(f"SISBEN APROXIMADO: Grupo {session.sisben_aproximado}")

    # Beneficios identificados
    if session.beneficios_identificados:
        parts.append(f"BENEFICIOS PREVIAMENTE IDENTIFICADOS: {', '.join(session.beneficios_identificados)}")

    # Análisis de imagen si existe
    if session.profile.analisis_imagen:
        parts.append(f"ANÁLISIS DE IMAGEN DE VIVIENDA:\n{session.profile.analisis_imagen}")

    # RAG: documentos relevantes
    rag_context = retrieve(user_message)
    if rag_context:
        parts.append(f"DOCUMENTOS DE REFERENCIA OFICIAL:\n{rag_context}")

    return "\n\n".join(parts)


def _update_profile_from_response(session: Session) -> None:
    """
    Actualiza el SISBEN aproximado y beneficios cuando hay datos suficientes.
    Se activa cuando el perfil tiene al menos 4 campos relevantes completos.
    """
    profile = session.profile
    filled = sum(
        1 for v in [
            profile.edad, profile.situacion_laboral, profile.ingreso_mensual_aprox,
            profile.material_piso, profile.acceso_agua_potable, profile.tenencia_vivienda,
            profile.es_mujer_cabeza_hogar, profile.num_personas_hogar
        ]
        if v is not None
    )

    if filled >= 3 and not session.sisben_aproximado:
        grupo, _ = aproximar_grupo_sisben(profile)
        session.sisben_aproximado = grupo
        matched = match_benefits(profile, grupo)
        session.beneficios_identificados = [b["id"] for b in matched]


async def process_message(session: Session, user_message: str) -> str:
    """Procesa un mensaje de texto y retorna la respuesta del agente."""
    session.add_message("user", user_message)
    _update_profile_from_response(session)

    if not settings.has_claude:
        reply = _FALLBACK_RESPONSE if not session.history else (
            "Para darte una orientación personalizada, necesito la API key de Claude configurada. "
            "Por favor revisa el archivo .env y agrega tu ANTHROPIC_API_KEY."
        )
        session.add_message("assistant", reply)
        return reply

    context = _build_context(session, user_message)

    messages = session.get_recent_history(n=12)
    if context:
        # Inyectamos el contexto en el último mensaje del usuario
        messages = messages[:-1] + [{
            "role": "user",
            "content": f"{context}\n\nMENSAJE DEL USUARIO: {user_message}"
        }]

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=_SYSTEM_PROMPT,
        messages=messages,
    )

    reply = response.content[0].text
    session.add_message("assistant", reply)
    return reply


async def process_image_message(session: Session, image_base64: str, caption: str = "") -> str:
    """Procesa un mensaje con imagen (foto de la vivienda)."""
    from app.vision.analyzer import analyze_house_image

    analysis = await analyze_house_image(image_base64)
    session.profile.imagen_vivienda_analizada = True
    session.profile.analisis_imagen = analysis

    context_msg = caption or "El usuario compartió una foto de su vivienda."
    full_message = f"{context_msg}\n\n[ANÁLISIS AUTOMÁTICO DE LA IMAGEN]:\n{analysis}"

    return await process_message(session, full_message)
