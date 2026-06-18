const { getSession, updateSession, resetSession, STATES } = require('./sessionManager');
const { runPrediction } = require('./flowiseClient');

const MESSAGES = {
  welcome: '¡Hola! Soy *EduRoute AI* 🎓\n\nCuéntame tu situación con libertad y te orientaré.',
  error: 'Hubo un problema temporal procesando tu solicitud. Intenta de nuevo en unos segundos o escribe *"reiniciar"* para comenzar.',
  reset: 'Listo, empecemos de nuevo.\n\n¡Hola! Soy *EduRoute AI* 🎓\nCuéntame tu situación con libertad.',
};

const RESET_COMMANDS = new Set(['reiniciar', 'reset']);

async function processMessage(sessionId, userMessage) {
  const msg = userMessage.trim();

  if (RESET_COMMANDS.has(msg.toLowerCase())) {
    resetSession(sessionId);
    return { reply: MESSAGES.reset, state: STATES.WELCOME };
  }

  const session = getSession(sessionId);

  if (session.state === STATES.WELCOME) {
    updateSession(sessionId, {
      state: STATES.OPEN_CHAT,
      history: [{ role: 'assistant', content: MESSAGES.welcome }],
    });
    return { reply: MESSAGES.welcome, state: STATES.OPEN_CHAT };
  }

  try {
    const aiReply = await runPrediction({ question: msg, history: session.history, sessionId });

    updateSession(sessionId, {
      state: STATES.FOLLOWUP,
      history: [
        ...session.history,
        { role: 'user', content: msg },
        { role: 'assistant', content: aiReply },
      ],
    });

    return { reply: aiReply, state: STATES.FOLLOWUP };
  } catch (err) {
    console.error('[ConversationFlow] AI error:', err.message);
    return { reply: MESSAGES.error, state: session.state };
  }
}

module.exports = { processMessage, MESSAGES };
