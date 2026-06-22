const { getSession, updateSession, resetSession, STATES } = require('./sessionManager');
const { generateResponse, generateFollowup } = require('./aiClient');

const MESSAGES = {
  welcome: `¡Hola! Soy *Tara AI* 🎓

Cuéntame tu situación con libertad y te orientaré.`,

  error: () =>
    `Hubo un problema temporal procesando tu solicitud. Intenta de nuevo en unos segundos o escribe *"reiniciar"* para comenzar.`,

  reset: () =>
    `Listo, empecemos de nuevo.\n\n¡Hola! Soy *Tara AI* 🎓\nCuéntame tu situación con libertad.`,
};

async function processMessage(sessionId, userMessage) {
  const msg = userMessage.trim();

  if (msg.toLowerCase() === 'reiniciar' || msg.toLowerCase() === 'reset') {
    resetSession(sessionId);
    return { reply: MESSAGES.reset(), state: STATES.WELCOME };
  }

  let session = getSession(sessionId);

  if (session.state === STATES.WELCOME) {
    session = updateSession(sessionId, {
      state: STATES.OPEN_CHAT,
      history: [...session.history, { role: 'assistant', content: MESSAGES.welcome }],
    });

    return { reply: MESSAGES.welcome, state: STATES.OPEN_CHAT };
  }

  if (session.state === STATES.OPEN_CHAT) {
    try {
      const aiReply = await generateResponse(
        msg,
        session.history,
        sessionId
      );

      updateSession(sessionId, {
        state: STATES.FOLLOWUP,
        history: [
          ...session.history,
          { role: 'assistant', content: aiReply },
        ],
      });

      return { reply: aiReply, state: STATES.FOLLOWUP };
    } catch (err) {
      console.error('AI error:', err.message);
      return { reply: MESSAGES.error(), state: STATES.OPEN_CHAT };
    }
  }

  if (session.state === STATES.FOLLOWUP) {
    try {
      const aiReply = await generateFollowup(
        msg,
        session.history,
        sessionId
      );

      updateSession(sessionId, {
        history: [
          ...session.history,
          { role: 'user', content: msg },
          { role: 'assistant', content: aiReply },
        ],
      });

      return { reply: aiReply, state: STATES.FOLLOWUP };
    } catch (err) {
      console.error('AI error:', err.message);
      return { reply: MESSAGES.error(), state: session.state };
    }
  }

  return { reply: MESSAGES.welcome, state: STATES.OPEN_CHAT };
}

module.exports = { processMessage, MESSAGES };
