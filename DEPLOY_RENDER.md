Render deployment checklist for EduRuta AI

1) Connect repo to Render
- In Render dashboard: New -> Web Service -> Connect GitHub/GitLab
- Select repo `webhook-whatsapp-api` and branch (e.g., `main`)

2) Service settings
- Name: eduruta-ai (or your preferred name)
- Environment: Node
- Build Command: (leave blank) or `npm install`
- Start Command: `npm start` (or `node app.js`)
- Instance type: Starter or Standard depending on expected traffic
- Auto Deploy: On (optional)

3) Environment Variables (Environment -> Environment Variables)
- PORT: 3000 (optional, Render sets it automatically)
- VERIFY_TOKEN: your_webhook_verify_token_here
- FLOWISE_URL: https://tu-instancia-flowise.com
- FLOWISE_FLOW_ID: tu-chatflow-id
- FLOWISE_API_KEY: (si aplica)
- FLOWISE_TIMEOUT_MS: 15000
- WHATSAPP_TOKEN: your_whatsapp_token_here
- WHATSAPP_PHONE_ID: your_phone_number_id_here
- NODE_ENV: production
- REDIS_URL: redis://:password@host:port (optional, si usas Redis)

4) Health check
- Render usually performs health checks on `/` or `/health`.
- We added `/health` endpoint. Set Health Check Path to `/health`.

5) Redis (optional)
- If necesitas persistencia de sesiones, crea un servicio Redis en Render y copia `REDIS_URL` a las Environment Variables.
- Actualiza `src/sessionManager.js` para usar Redis (si no lo has hecho todavía).

6) Webhook configuration
- Copia la URL pública de tu servicio en Render: `https://<your-service>.onrender.com/webhook`
- En la consola de Meta/WhatsApp Cloud, configura el webhook con esa URL y `VERIFY_TOKEN`.

7) Logs y debugging
- Usa Render Dashboard -> Logs para ver llamadas entrantes, errores y llamadas a Flowise.
- Incrementa `FLOWISE_TIMEOUT_MS` si tu instancia Flowise es lenta.

8) Rollout
- Habilita auto-deploy para deploys automáticos desde `main`.
- Para rollback, usa Git tags/branches o Render dashboard para desplegar un commit anterior.

9) Post-deploy tests
- Test Flowise direct call (curl) — ver `FLOWISE_PROMPT.md` for the sample payload.
- Test server endpoint:
  ```bash
  curl -X GET https://<your-service>.onrender.com/health
  ```
- Test `/api/chat` (POST) with a sessionId and message to simulate a user.

10) Security
- No subir `.env` al repo.
- Mantener `FLOWISE_API_KEY` y `WHATSAPP_TOKEN` como secrets en Render.

If you want, I can also:
- prepare a `redis`-backed `sessionManager` implementation,
- or commit a small `deploy.sh` with Render CLI commands.
