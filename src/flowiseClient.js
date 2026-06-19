const axios = require('axios');

function hasFlowiseConfig() {
  return Boolean(process.env.FLOWISE_URL && process.env.FLOWISE_FLOW_ID);
}

function buildHistory(history = []) {
  return history
    .filter((item) => item && item.role && item.content)
    .map((item) => ({
      role: item.role === 'assistant' ? 'apiMessage' : 'userMessage',
      content: String(item.content),
    }));
}

function buildPredictionBody({ question, history = [], sessionId = null }) {
  return {
    question,
    streaming: false,
    history: buildHistory(history),
    overrideConfig: { sessionId },
    uploads: [],
    form: {},
    humanInput: {},
  };
}

function normalizePredictionResponse(data) {
  if (!data) return '';
  if (typeof data.text === 'string' && data.text.trim()) return data.text.trim();
  if (typeof data.result === 'string' && data.result.trim()) return data.result.trim();
  if (typeof data.output === 'string' && data.output.trim()) return data.output.trim();
  if (typeof data.answer === 'string' && data.answer.trim()) return data.answer.trim();
  if (typeof data.message === 'string' && data.message.trim()) return data.message.trim();
  if (typeof data.response === 'string' && data.response.trim()) return data.response.trim();
  // Respuesta anidada: { outputs: [{ text: "..." }] }
  if (Array.isArray(data.outputs) && data.outputs.length > 0) {
    const first = data.outputs[0];
    const nested = first?.text || first?.result || first?.output || first?.answer;
    if (typeof nested === 'string' && nested.trim()) return nested.trim();
  }
  console.error('[Flowise] Estructura de respuesta no reconocida:', JSON.stringify(data));
  return '';
}

async function runPrediction({ question, history = [], sessionId = null }) {
  if (!hasFlowiseConfig()) {
    throw new Error('Flowise no está configurado');
  }

  const baseUrl = process.env.FLOWISE_URL.replace(/\/$/, '');
  const flowId = process.env.FLOWISE_FLOW_ID;
  const apiKey = process.env.FLOWISE_API_KEY;

  const body = buildPredictionBody({ question, history, sessionId });
  console.log('[Flowise] Enviando a:', `${baseUrl}/api/v1/prediction/${flowId}`);
  console.log('[Flowise] Body enviado:', JSON.stringify(body));

  let response;
  try {
    response = await axios.post(
      `${baseUrl}/api/v1/prediction/${flowId}`,
      body,
      {
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
        },
        timeout: Number(process.env.FLOWISE_TIMEOUT_MS || 30000),
      }
    );
  } catch (err) {
    if (err.response) {
      console.error('[Flowise] Error HTTP:', err.response.status);
      console.error('[Flowise] Respuesta de error:', JSON.stringify(err.response.data));
    } else if (err.code === 'ECONNABORTED') {
      console.error('[Flowise] Timeout — FLOWISE_TIMEOUT_MS:', process.env.FLOWISE_TIMEOUT_MS || 15000);
    } else {
      console.error('[Flowise] Error de red:', err.message);
    }
    throw err;
  }

  console.log('[Flowise] HTTP status:', response.status);
  console.log('[Flowise] Respuesta data:', JSON.stringify(response.data));
  const text = normalizePredictionResponse(response.data);
  if (!text) {
    throw new Error('Flowise no devolvió un campo de texto utilizable');
  }

  return text;
}

module.exports = {
  hasFlowiseConfig,
  buildHistory,
  buildPredictionBody,
  normalizePredictionResponse,
  runPrediction,
};