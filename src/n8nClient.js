const axios = require('axios');

function hasN8nConfig() {
  return Boolean(process.env.N8N_WEBHOOK_URL);
}

function buildHistory(history = []) {
  return history
    .filter((item) => item && item.role && item.content)
    .map((item) => ({
      role: item.role === 'assistant' ? 'assistant' : 'user',
      content: String(item.content),
    }));
}

function buildWebhookBody({ question, history = [], sessionId = null }) {
  return {
    question,
    history: buildHistory(history),
    sessionId,
  };
}

function normalizeN8nResponse(data) {
  if (!data) return '';

  if (typeof data === 'string' && data.trim()) return data.trim();

  const candidates = [
    data.text,
    data.result,
    data.output,
    data.answer,
    data.message,
    data.response,
    data.body,
    data.data,
    data.json,
    data.payload,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim();
    }

    if (candidate && typeof candidate === 'object') {
      const nested = normalizeN8nResponse(candidate);
      if (nested) return nested;
    }
  }

  if (Array.isArray(data) && data.length > 0) {
    for (const item of data) {
      const nested = normalizeN8nResponse(item);
      if (nested) return nested;
    }
  }

  console.error('[n8n] Estructura de respuesta no reconocida:', JSON.stringify(data));
  return '';
}

async function runPrediction({ question, history = [], sessionId = null }) {
  if (!hasN8nConfig()) {
    throw new Error('n8n no está configurado');
  }

  const webhookUrl = process.env.N8N_WEBHOOK_URL;
  const apiKey = process.env.N8N_API_KEY;
  const body = buildWebhookBody({ question, history, sessionId });

  console.log('[n8n] Enviando a:', webhookUrl);
  console.log('[n8n] Body enviado:', JSON.stringify(body));

  let response;
  try {
    response = await axios.post(webhookUrl, body, {
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
      timeout: Number(process.env.N8N_TIMEOUT_MS || 30000),
    });
  } catch (err) {
    if (err.response) {
      console.error('[n8n] Error HTTP:', err.response.status);
      console.error('[n8n] Respuesta de error:', JSON.stringify(err.response.data));
    } else if (err.code === 'ECONNABORTED') {
      console.error('[n8n] Timeout — N8N_TIMEOUT_MS:', process.env.N8N_TIMEOUT_MS || 30000);
    } else {
      console.error('[n8n] Error de red:', err.message);
    }
    throw err;
  }

  console.log('[n8n] HTTP status:', response.status);
  console.log('[n8n] Respuesta data:', JSON.stringify(response.data));

  const text = normalizeN8nResponse(response.data);
  if (!text) {
    throw new Error('n8n no devolvió un campo de texto utilizable');
  }

  return text;
}

module.exports = {
  hasN8nConfig,
  buildHistory,
  buildWebhookBody,
  normalizeN8nResponse,
  runPrediction,
};