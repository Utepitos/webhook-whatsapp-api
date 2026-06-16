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

function buildPredictionBody({ question, knowledgeContext, history = [], matches = [], profile = {}, sessionId = null }) {
  return {
    question,
    streaming: false,
    history: buildHistory(history),
    overrideConfig: {
      sessionId,
      vars: {
        knowledgeContext,
        profile: JSON.stringify(profile),
        matches: JSON.stringify(matches),
      },
    },
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
  return '';
}

async function runPrediction({ question, knowledgeContext, history = [], matches = [], profile = {}, sessionId = null }) {
  if (!hasFlowiseConfig()) {
    throw new Error('Flowise no está configurado');
  }

  const baseUrl = process.env.FLOWISE_URL.replace(/\/$/, '');
  const flowId = process.env.FLOWISE_FLOW_ID;
  const apiKey = process.env.FLOWISE_API_KEY;

  const response = await axios.post(
    `${baseUrl}/api/v1/prediction/${flowId}`,
    buildPredictionBody({ question, knowledgeContext, history, matches, profile, sessionId }),
    {
      headers: {
        'Content-Type': 'application/json',
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
      timeout: Number(process.env.FLOWISE_TIMEOUT_MS || 15000),
    }
  );

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