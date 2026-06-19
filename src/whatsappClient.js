const axios = require('axios');

async function sendMessage(to, text) {
  const token = process.env.WHATSAPP_TOKEN;
  const phoneId = process.env.WHATSAPP_PHONE_ID;

  if (!token || !phoneId) {
    console.log('[WhatsApp] Modo demo - mensaje no enviado:', text.slice(0, 80) + '...');
    return;
  }

  try {
    const response = await axios.post(
      `https://graph.facebook.com/v19.0/${phoneId}/messages`,
      {
        messaging_product: 'whatsapp',
        to,
        type: 'text',
        text: { body: text },
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    console.log('[Meta] Mensaje enviado OK, status:', response.status);
  } catch (err) {
    if (err.response) {
      console.error('[Meta] Error HTTP:', err.response.status);
      console.error('[Meta] Detalle:', JSON.stringify(err.response.data));
    } else {
      console.error('[Meta] Error de red:', err.message);
    }
    throw err;
  }
}

function extractMessage(body) {
  try {
    const entry = body.entry?.[0];
    const change = entry?.changes?.[0];
    const message = change?.value?.messages?.[0];
    if (!message) return null;

    return {
      from: message.from,
      text: message.text?.body || '',
      type: message.type,
      messageId: message.id,
    };
  } catch {
    return null;
  }
}

module.exports = { sendMessage, extractMessage };
