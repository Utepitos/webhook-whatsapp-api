# BeneficiosYA AI 🇨🇴

> Agente de WhatsApp que orienta a ciudadanos colombianos en situación de vulnerabilidad sobre los beneficios y programas del gobierno a los que tienen derecho.

---

## El problema

Millones de colombianos en situación de pobreza o vulnerabilidad no acceden a los beneficios estatales que les corresponden, no por falta de elegibilidad, sino por **falta de información**:

- No saben que existen programas como Familias en Acción, Colombia Mayor o el régimen subsidiado de salud
- No conocen los requisitos ni los pasos para aplicar
- No tienen a nadie que los oriente de forma personalizada y accesible
- La información oficial está fragmentada en múltiples sitios gubernamentales

**BeneficiosYA resuelve esto con un chatbot de WhatsApp**, el canal de comunicación más usado en Colombia, especialmente en sectores populares.

---

## Solución

Un agente de IA conversacional que:

1. **Escucha** la situación del ciudadano en lenguaje natural
2. **Analiza** su perfil (composición familiar, condiciones de vivienda, situación económica)
3. **Estima** su probable grupo SISBEN con base en criterios objetivos
4. **Identifica** los programas y subsidios a los que puede acceder
5. **Guía** paso a paso cómo aplicar a cada beneficio
6. **Analiza fotos** de la vivienda para complementar la evaluación

---

## Demo — Caso de uso

**Escenario:** María, 34 años, madre soltera, vive en Soacha con sus 3 hijos (7, 12 y 16 años). Trabaja como vendedora informal. Vive en casa arrendada con paredes de bloque sin revocar y piso de cemento.

```
María: Hola, estoy buscando ayuda del gobierno para mis hijos
BeneficiosYA: Hola María, con gusto te ayudo. Cuéntame un poco,
             ¿cuántos años tienes y cuántas personas viven contigo?

María: Tengo 34, vivo con mis 3 hijos de 7, 12 y 16 años. Soy sola.

BeneficiosYA: Entiendo tu situación. Como madre cabeza de hogar con 3 hijos,
             hay varios programas importantes para ti.
             ¿Actualmente tienes algún puntaje SISBEN o tarjeta del gobierno?

María: No sé qué es eso

BeneficiosYA: No te preocupes, te explico. El SISBEN es un registro
             del gobierno para saber quién necesita ayuda...
             [continúa recopilando información y orientando]

--- Respuesta final ---
Según tu perfil, identifico que puedes acceder a:

1. FAMILIAS EN ACCIÓN — Transferencia bimestral por tus 3 hijos
   → Hasta ~$215.000 COP bimestrales
   
2. RÉGIMEN SUBSIDIADO DE SALUD — Salud gratis para toda la familia
   → Afíliate en la Alcaldía de Soacha
   
3. PAE — Alimentación escolar gratuita para tus dos hijos en colegio público

4. JÓVENES EN ACCIÓN — Tu hijo de 16 puede acceder cuando entre al SENA

PRÓXIMOS PASOS:
1. Ve a la Alcaldía de Soacha y solicita la encuesta SISBEN
2. Con el puntaje SISBEN, inscríbete en Familias en Acción: prosperidadsocial.gov.co
3. Afilia a la familia al régimen subsidiado en la Secretaría de Salud
```

---

## Arquitectura

```
WhatsApp Cloud API
        ↓
   FastAPI Webhook
        ↓
   ┌────────────────────────────┐
   │        Agente AI           │
   │  ┌──────────────────────┐  │
   │  │   Sesión del usuario │  │  ← Historial + perfil acumulado
   │  └──────────────────────┘  │
   │  ┌──────────────────────┐  │
   │  │   SISBEN Estimator   │  │  ← Reglas basadas en criterios DANE
   │  └──────────────────────┘  │
   │  ┌──────────────────────┐  │
   │  │   Benefits Matcher   │  │  ← 15+ programas gubernamentales
   │  └──────────────────────┘  │
   │  ┌──────────────────────┐  │
   │  │   RAG (BM25)         │  │  ← Documentos oficiales SISBEN/DPS
   │  └──────────────────────┘  │
   │  ┌──────────────────────┐  │
   │  │   Vision (Claude)    │  │  ← Análisis de fotos de vivienda
   │  └──────────────────────┘  │
   └────────────────────────────┘
        ↓
   Claude Sonnet (LLM)
        ↓
   Respuesta personalizada → WhatsApp
```

---

## Stack tecnológico

| Componente | Tecnología |
|-----------|------------|
| Backend | Python 3.11 + FastAPI |
| LLM | Claude Sonnet (Anthropic) |
| Visión | Claude Vision (análisis de imágenes) |
| RAG | BM25Okapi (rank-bm25) |
| Canal | WhatsApp Cloud API (Meta) |
| Sesiones | In-memory (prod: Redis) |

---

## Instalación y ejecución

### Requisitos
- Python 3.11+
- Cuenta de Anthropic con API key
- (Opcional) Cuenta de Meta for Developers para WhatsApp real

### Setup

```bash
# 1. Clonar el repositorio
git clone https://github.com/Utepitos/webhook-whatsapp-api
cd BeneficiosYA

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar tu ANTHROPIC_API_KEY

# 5. (Opcional) Agregar documentos oficiales
# Ver documentos/COMO_AGREGAR_DOCUMENTOS.md

# 6. Iniciar el servidor
python main.py
```

El servidor queda disponible en `http://localhost:8000`

### Probar sin WhatsApp (API REST)

```bash
# Iniciar conversación
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo_001", "message": "Hola, necesito ayuda del gobierno"}'

# Continuar conversación
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo_001", "message": "Tengo 3 hijos, vivo en Bogotá y trabajo informal"}'

# Documentación interactiva
# http://localhost:8000/docs
```

---

## Ejecutar tests

```bash
# Todos los tests
pytest tests/ -v

# Tests por módulo
pytest tests/test_sisben.py -v
pytest tests/test_benefits.py -v
pytest tests/test_rag.py -v
pytest tests/test_agent.py -v
pytest tests/test_webhook.py -v

# Con cobertura
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Módulos principales

| Módulo | Descripción |
|--------|-------------|
| `app/agent/chatbot.py` | Orquestador principal del agente |
| `app/agent/sisben.py` | Estimación del grupo SISBEN con base en perfil |
| `app/agent/benefits.py` | Matching de beneficios según perfil y SISBEN |
| `app/agent/session.py` | Gestión de sesiones y perfil del usuario |
| `app/rag/` | Sistema RAG con BM25 para documentos oficiales |
| `app/vision/analyzer.py` | Análisis de imágenes de vivienda con Claude Vision |
| `app/whatsapp/` | Integración con WhatsApp Cloud API |

---

## Agregar documentos oficiales (RAG)

El agente mejora significativamente cuando tiene acceso a documentos oficiales. Ver instrucciones en `documents/COMO_AGREGAR_DOCUMENTOS.md`.

Los documentos se procesan automáticamente al arrancar el servidor. Formatos soportados: `.pdf`, `.txt`, `.md`.

---

## Programas gubernamentales incluidos

| Programa | Entidad | Grupo SISBEN |
|----------|---------|-------------|
| Familias en Acción | DPS | A, B |
| Colombia Mayor | Colpensiones | A, B |
| Jóvenes en Acción | DPS | A, B, C |
| Ingreso Solidario | DPS | A, B |
| Régimen Subsidiado de Salud | MinSalud | A, B, C |
| PAE - Alimentación Escolar | MinEducación | Todos |
| Matrícula Cero | MinEducación | A, B, C |
| Generación E | MinEducación | A, B |
| Mi Casa Ya | MinVivienda | A, B, C |
| Subsidio Vivienda Rural | MinVivienda | A, B |
| Subsidio Servicios Públicos | SSPD | A, B |
| Programas ICBF | ICBF | A, B, C |
| Atención Víctimas | UARIV | A, B, C |
| Personas con Discapacidad | MinSalud | A, B, C |
| Formación SENA | SENA | Todos |
| BEPS | Colpensiones | A, B, C |

---

## Configurar WhatsApp real

1. Crear app en [Meta for Developers](https://developers.facebook.com)
2. Habilitar WhatsApp Business API
3. Obtener `WHATSAPP_TOKEN` y `WHATSAPP_PHONE_ID`
4. Configurar webhook URL: `https://tu-dominio.com/webhook`
5. Verificar con el token configurado en `.env`

Para exponer localhost en desarrollo: usar [ngrok](https://ngrok.com) o similar.

---

## Roadmap (post-hackathon)

- [ ] Integración con API oficial del SISBEN para consulta de puntaje real
- [ ] Base de datos persistente (PostgreSQL + Redis para sesiones)
- [ ] Detección de municipio por geolocalización
- [ ] Soporte multilenguaje (lenguas indígenas)
- [ ] Panel de administración para actualizar programas
- [ ] Notificaciones proactivas sobre nuevas convocatorias
- [ ] Integración con sistema de citas en entidades gubernamentales

---

## Equipo

Desarrollado durante hackathon 2024 — Rama Fernando

---

*BeneficiosYA es una herramienta de orientación. La información provista es de carácter informativo y el ciudadano debe verificar su elegibilidad directamente con las entidades gubernamentales.*
