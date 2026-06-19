require('dotenv').config();
const express = require('express');
const { sendMessage, extractMessage } = require('./src/whatsappClient');
const { runPrediction } = require('./src/n8nClient');

const app = express();
app.use(express.json());

const port = process.env.PORT || 3000;
const verifyToken = process.env.VERIFY_TOKEN;

app.use((req, res, next) => {
  if (req.path === '/webhook') {
    console.log(`[Webhook] ${req.method} ${req.originalUrl}`);
  }
  next();
});

// WhatsApp webhook verification
app.get('/webhook', (req, res) => {
  const { 'hub.mode': mode, 'hub.challenge': challenge, 'hub.verify_token': token } = req.query;
  console.log('[Webhook] Verificación recibida', {
    mode,
    hasChallenge: Boolean(challenge),
    tokenMatches: token === verifyToken,
  });
  if (mode === 'subscribe' && token === verifyToken) {
    console.log('Webhook verificado');
    return res.status(200).send(challenge);
  }
  res.status(403).end();
});

// WhatsApp webhook messages
app.post('/webhook', async (req, res) => {
  res.status(200).end();

  const incoming = extractMessage(req.body);
  if (!incoming || incoming.type !== 'text') return;

  console.log(`[WhatsApp] Mensaje de ${incoming.from}: ${incoming.text}`);

  try {
    const reply = await runPrediction({ question: incoming.text, sessionId: incoming.from });
    await sendMessage(incoming.from, reply);
  } catch (err) {
    console.error('Error procesando mensaje:', err.message);
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/', (req, res) => {
  res.json({ service: 'EduRoute AI', status: 'running' });
});

app.listen(port, () => {
  console.log(`Webhook URL: http://localhost:${port}/webhook\n`);
});
