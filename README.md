# EduRuta AI

Servidor Node.js para recibir mensajes de WhatsApp, enviarlos a Flowise y devolver orientación educativa por chat.

## Flujo

Usuario -> WhatsApp -> API de WhatsApp -> servidor -> Flowise -> servidor -> API de WhatsApp -> usuario.

## Variables de entorno

- `PORT`
- `VERIFY_TOKEN`
- `FLOWISE_URL`
- `FLOWISE_FLOW_ID`
- `FLOWISE_API_KEY`
- `FLOWISE_TIMEOUT_MS`
- `WHATSAPP_TOKEN`
- `WHATSAPP_PHONE_ID`

## Ejecutar

```bash
npm install
npm run smoke
npm run dev
```

## Contrato Flowise

El servidor llama `POST /api/v1/prediction/{flowId}` con `question`, `history` y `overrideConfig.vars`.

Si Flowise falla, el servidor usa respuestas deterministas locales (fallback) en lugar de una API externa.

## Plantilla de prompt para Flowise

He incluido una plantilla de prompt optimizada para EduRuta en el archivo `FLOWISE_PROMPT.md`. Esa plantilla contiene:

- El `system prompt` (tono y reglas de comportamiento).
- Formato de respuesta esperado (opciones numeradas, documentos, próximos pasos, mensaje motivador).
- Variables `overrideConfig.vars` esperadas: `knowledgeContext`, `profile`, `matches`, `history`, `sessionId`.
- Sugerencias de configuración del LLM: `temperature: 0.0-0.3`, `max_tokens`, y guardrails para evitar alucinaciones.

Revisa `FLOWISE_PROMPT.md` y pega ese texto en el nodo de generación de tu flow en Flowise (el que tu compañero ya creó).

## Despliegue y testeo

1) Preparar entorno:

```bash
cp .env.example .env
# Edita .env con tus valores reales: FLOWISE_URL, FLOWISE_FLOW_ID, FLOWISE_API_KEY, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, VERIFY_TOKEN
npm install
```

2) Ejecutar localmente:

```bash
npm run dev
```

3) Probar la integración Flowise directamente (prueba rápida con curl):

Reemplaza `${FLOWISE_URL}` y `${FLOWISE_FLOW_ID}` en el siguiente comando y asegúrate de tener `FLOWISE_API_KEY` si tu instancia lo requiere.

```bash
curl -X POST "${FLOWISE_URL}/api/v1/prediction/${FLOWISE_FLOW_ID}" \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer ${FLOWISE_API_KEY}" \
	-d '{
		"question": "Prueba: dame 2 opciones para alguien de 18 años en Boyacá que no puede pagar",
		"history": [],
		"stream": false,
		"overrideConfig": {
			"vars": {
				"knowledgeContext": "[TEXTO_CON_PROGRAMAS_VERIFICADOS]",
				"profile": {"age":18,"department":"Boyacá","canPay":false},
				"matches": []
			},
			"sessionId": "session-test-1"
		}
	}'
```

4) Probar el servidor localmente con ngrok (para simular webhook de WhatsApp):

```bash
# instala ngrok y expon el puerto 3000
ngrok http 3000
# copia la URL HTTPS que te da ngrok y configúrala como webhook en la consola de Facebook/Meta
```

5) Verifica que el webhook reciba mensajes y que el servidor haga la llamada a Flowise (revisar logs). Las rutas útiles son `/webhook` y `/api/chat` (si activaste endpoints de prueba).

6) Despliegue en producción (Render / Heroku / VPS):

- Subir código a tu repositorio y en el servicio de hosting configurar las variables de entorno del proyecto con los valores de `FLOWISE_*` y `WHATSAPP_*`.
- Asegúrate de tener un certificado TLS (Render/Heroku lo proveen) y que la URL pública esté configurada como webhook en la app de WhatsApp Cloud.
- Ajusta `FLOWISE_TIMEOUT_MS` según latencia de tu instancia Flowise.

6) Monitoreo y seguridad:

- Mantén `temperature` bajo en Flowise.
- Anota logs de llamadas a Flowise y errores para detectar fallos.
- Considera persistir sesiones en Redis si tu despliegue será multi-instancia.

## Despliegue en Render con Blueprint

Si vas a usar Render, ya tienes un blueprint listo en `render.yaml`.

Pasos:

1. Sube este repo a GitHub.
2. En Render, elige `New` -> `Blueprint`.
3. Conecta el repo y selecciona la rama principal.
4. Render leerá `render.yaml` y creará el servicio `eduruta-ai`.
5. Completa las variables marcadas como secretas:
	- `VERIFY_TOKEN`
	- `FLOWISE_URL`
	- `FLOWISE_FLOW_ID`
	- `FLOWISE_API_KEY` si aplica
	- `WHATSAPP_TOKEN`
	- `WHATSAPP_PHONE_ID`
6. Verifica que el health check use `/health`.
7. Copia la URL pública y configúrala como webhook en Meta/WhatsApp: `https://<tu-servicio>.onrender.com/webhook`.

Ventaja del blueprint:
- Te evita configurar manualmente build/start commands.
- Deja el despliegue reproducible y versionado junto al código.

Archivos de apoyo para Render:
- `RENDER_ENV_VARS.md`: lista exacta de variables para copiar y pegar.
- `POST_DEPLOY_RENDER_CHECKLIST.md`: verificación rápida después del deploy.

Si quieres, puedo:
- pegar el contenido listo para el nodo de LLM en Flowise (formato copia/pega),
- o generar un `post-deploy checklist` con pasos exactos para Render/Heroku.

-- Guía específica para Render

He añadido `DEPLOY_RENDER.md` con una checklist paso a paso para desplegar en Render (con variables de entorno, health check, Redis opcional y pruebas post-deploy).

Consulta `DEPLOY_RENDER.md` para la guía completa.