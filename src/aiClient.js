const { runPrediction, hasFlowiseConfig } = require('./flowiseClient');

function fallbackTemporaryError() {
  return 'Lo siento, tuve un problema temporal al consultar la información. Intenta de nuevo en unos segundos o escribe "reiniciar" para empezar otra vez.';
}

async function generateResponse(userMessage, history = [], sessionId = null) {
  if (hasFlowiseConfig()) {
    try {
      return await runPrediction({
        question: userMessage,
        history,
        sessionId,
      });
    } catch (err) {
      console.error('[Flowise] Error ejecutando predicción:', err.message);
      return fallbackTemporaryError();
    }
  }

  return fallbackTemporaryError();
}

async function generateFollowup(userQuestion, history = [], sessionId = null) {
  if (hasFlowiseConfig()) {
    try {
      return await runPrediction({
        question: userQuestion,
        history,
        sessionId,
      });
    } catch (err) {
      console.error('[Flowise] Error ejecutando seguimiento:', err.message);
      return fallbackTemporaryError();
    }
  }

  return fallbackTemporaryError();
}

module.exports = { generateResponse, generateFollowup };
