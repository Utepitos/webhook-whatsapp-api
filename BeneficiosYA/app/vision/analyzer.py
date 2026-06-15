"""
Análisis de imágenes de vivienda usando Claude Vision.
Identifica condiciones del hogar para complementar la aproximación SISBEN.
"""

import anthropic
from app.config import settings

VISION_PROMPT = """Analiza esta imagen de vivienda de una familia colombiana en situación de vulnerabilidad.

Identifica y describe lo siguiente (sé objetivo y respetuoso):

1. MATERIAL DE PAREDES: ¿De qué están hechas? (ladrillo, bloque, madera, zinc, bahareque, cartón, etc.)
2. MATERIAL DEL TECHO: ¿Qué tipo de techo se observa? (losa, zinc, teja, paja, plástico, etc.)
3. MATERIAL DEL PISO: ¿Qué tipo de piso se ve? (tierra, cemento, baldosa, madera, etc.)
4. ESTADO GENERAL: ¿La vivienda parece en buen, regular o mal estado?
5. HACINAMIENTO: ¿Parece haber muchas personas o cosas en poco espacio?
6. SERVICIOS VISIBLES: ¿Se observa energía eléctrica, agua, etc.?
7. ENTORNO: ¿Es zona urbana, rural, asentamiento informal?

Responde en formato estructurado y con lenguaje técnico pero claro.
Al final, indica qué factores de esta imagen sugieren mayor o menor vulnerabilidad socioeconómica."""


async def analyze_house_image(image_base64: str, media_type: str = "image/jpeg") -> str:
    """
    Analiza una imagen de vivienda y retorna un análisis de las condiciones del hogar.
    """
    if not settings.has_claude:
        return "Análisis de imagen no disponible (se requiere API key de Claude)."

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }
        ],
    )

    return response.content[0].text
