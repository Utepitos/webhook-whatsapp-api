require('dotenv').config();
const crypto = require('crypto');
const express = require('express');
const { sendMessage, extractMessage } = require('./src/whatsappClient');
const { processMessage } = require('./src/conversationFlow');

const app = express();
const port = process.env.PORT || 3000;

app.use(
  express.json({
    verify: (req, _res, buf) => {
      req.rawBody = buf;
    },
  })
);

app.use((req, _res, next) => {
  if (req.path === '/webhook') {
    console.log(`[Webhook] ${req.method} ${req.originalUrl}`);
  }
  next();
});

function isValidWebhookSignature(rawBody, signature) {
  const secret = process.env.WHATSAPP_APP_SECRET;
  if (!secret) return true;
  if (!signature) return false;
  const expected = `sha256=${crypto.createHmac('sha256', secret).update(rawBody).digest('hex')}`;
  try {
    return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
  } catch {
    return false;
  }
}

app.get('/webhook', (req, res) => {
  const { 'hub.mode': mode, 'hub.challenge': challenge, 'hub.verify_token': token } = req.query;
  if (mode === 'subscribe' && token === process.env.VERIFY_TOKEN) {
    console.log('[Webhook] Verificación exitosa');
    return res.status(200).send(challenge);
  }
  res.status(403).end();
});

app.post('/webhook', async (req, res) => {
  if (!isValidWebhookSignature(req.rawBody, req.headers['x-hub-signature-256'])) {
    console.warn('[Webhook] Firma inválida — solicitud rechazada');
    return res.status(401).end();
  }

  res.status(200).end();

  const incoming = extractMessage(req.body);
  if (!incoming || incoming.type !== 'text') return;

  console.log(`[WhatsApp] Mensaje entrante de ${incoming.from}`);

  try {
    const { reply } = await processMessage(incoming.from, incoming.text);
    await sendMessage(incoming.from, reply);
  } catch (err) {
    console.error('[Webhook] Error procesando mensaje:', err.message);
  }
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/', (_req, res) => {
  res.json({ service: 'EduRoute AI', status: 'running' });
});

if (require.main === module) {
  app.listen(port, () => {
    console.log(`[App] Servidor iniciado — webhook: http://localhost:${port}/webhook`);
  });
}

module.exports = app;
