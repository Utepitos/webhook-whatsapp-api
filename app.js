require('dotenv').config();
const express = require('express');
const path = require('path');
const { processMessage, MESSAGES } = require('./src/conversationFlow');
const { sendMessage, extractMessage } = require('./src/whatsappClient');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const port = process.env.PORT || 3000;
const verifyToken = process.env.VERIFY_TOKEN || 'eduruta_demo_2024';

// WhatsApp webhook verification
app.get('/webhook', (req, res) => {
  const { 'hub.mode': mode, 'hub.challenge': challenge, 'hub.verify_token': token } = req.query;
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
    const { reply } = await processMessage(incoming.from, incoming.text);
    await sendMessage(incoming.from, reply);
  } catch (err) {
    console.error('Error procesando mensaje:', err.message);
  }
});

// API para el demo web
app.post('/api/chat', async (req, res) => {
  const { sessionId, message } = req.body;

  if (!sessionId || !message) {
    return res.status(400).json({ error: 'sessionId y message son requeridos' });
  }

  try {
    const result = await processMessage(sessionId, message);
    res.json(result);
  } catch (err) {
    console.error('Error en /api/chat:', err.message);
    res.status(500).json({ error: 'Error interno del servidor', detail: err.message });
  }
});

// Iniciar sesión de demo
app.post('/api/start', (req, res) => {
  const { sessionId } = req.body;
  if (!sessionId) return res.status(400).json({ error: 'sessionId requerido' });

  const { resetSession } = require('./src/sessionManager');
  resetSession(sessionId);

  res.json({ reply: MESSAGES.welcome, state: 'ASK_AGE' });
});

// Servir demo web
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, () => {
  console.log(`\nEduRuta AI corriendo en http://localhost:${port}`);
  console.log(`Demo web:     http://localhost:${port}/`);
  console.log(`Webhook URL:  http://localhost:${port}/webhook\n`);
});
