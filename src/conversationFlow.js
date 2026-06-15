const { getSession, updateSession, STATES } = require('./sessionManager');
const { matchPrograms, buildKnowledgeContext } = require('./knowledgeBase');
const { generateResponse, generateFollowup } = require('./aiClient');

const MESSAGES = {
  welcome: `¡Hola! Soy *EduRuta AI* 🎓

Te ayudo a encontrar oportunidades de educación superior gratuitas o de bajo costo en Colombia.

Cuéntame un poco sobre ti para encontrar las mejores opciones.

¿Cuántos años tienes?`,

  askLocation: (age) =>
    `Perfecto, ${age} años. ¿En qué departamento vives actualmente?`,

  askFamily: (dept) =>
    `Entendido, vives en ${dept}. ¿Cuál describe mejor tu situación familiar?\n\n1️⃣ Mamá o papá cabeza de hogar (familia de bajos recursos)\n2️⃣ Familia de bajos recursos (estrato 1 o 2)\n3️⃣ Familia de recursos medios (estrato 3)\n4️⃣ Mis padres trabajan formalmente (afiliados a caja de compensación)\n\nEscribe el número o descríbelo con tus palabras.`,

  askIncome: () =>
    `Gracias por contarme. ¿Puedes pagar la universidad por tu cuenta o con ayuda de tu familia?\n\n1️⃣ No, no tenemos recursos para pagarla\n2️⃣ Podríamos pagar algo, pero no el total\n3️⃣ Sí, podríamos costearla`,

  askIcfes: () =>
    `Entendido. ¿Ya tienes tu resultado de las pruebas ICFES (Saber 11)?\n\n• Si sí, dime tu puntaje total\n• Si aún no las has presentado, escribe *"no"*\n• Si las presentaste pero no recuerdas el puntaje, escribe *"no recuerdo"*`,

  analyzing: () =>
    `🔍 Analizando tu perfil y buscando las mejores opciones para ti...`,

  error: () =>
    `Hubo un problema procesando tu solicitud. ¿Quieres intentar de nuevo? Escribe *"reiniciar"* para comenzar.`,

  reset: () =>
    `Listo, empecemos de nuevo.\n\n¡Hola! Soy *EduRuta AI* 🎓\n¿Cuántos años tienes?`,
};

function parseFamily(input) {
  const i = input.trim().toLowerCase();
  if (i === '1' || i.includes('cabeza') || i.includes('madre sola') || i.includes('papa solo')) return 'cabeza_hogar';
  if (i === '2' || i.includes('bajos') || i.includes('estrato 1') || i.includes('estrato 2')) return 'bajo_recursos';
  if (i === '3' || i.includes('medios') || i.includes('estrato 3')) return 'recursos_medios';
  if (i === '4' || i.includes('formal') || i.includes('afiliado') || i.includes('caja')) return 'empleado_formal';
  return 'bajo_recursos';
}

function parseIncome(input) {
  const i = input.trim().toLowerCase();
  if (i === '1' || i.includes('no') || i.includes('sin recursos') || i.includes('no pued')) return 'no';
  if (i === '2' || i.includes('algo') || i.includes('parcial') || i.includes('poco')) return 'partial';
  if (i === '3' || i.includes('sí') || i.includes('si') || i.includes('pued')) return 'yes';
  return 'no';
}

function parseIcfes(input) {
  const i = input.trim().toLowerCase();
  if (i === 'no' || i.includes('no lo') || i.includes('aún no') || i.includes('todavía')) return '0';
  if (i.includes('no recuerdo') || i.includes('no me acuerdo')) return '0';
  const num = parseInt(i.replace(/[^0-9]/g, ''));
  return isNaN(num) ? '0' : String(num);
}

async function processMessage(sessionId, userMessage) {
  const msg = userMessage.trim();

  if (msg.toLowerCase() === 'reiniciar' || msg.toLowerCase() === 'reset') {
    const { resetSession } = require('./sessionManager');
    resetSession(sessionId);
    return { reply: MESSAGES.reset(), state: STATES.ASK_AGE };
  }

  let session = getSession(sessionId);

  if (session.state === STATES.WELCOME || session.state === STATES.ASK_AGE) {
    const age = parseInt(msg.replace(/[^0-9]/g, ''));
    if (isNaN(age) || age < 12 || age > 60) {
      return { reply: '¿Cuántos años tienes? Por favor escribe solo el número (ej: 17)', state: session.state };
    }
    session = updateSession(sessionId, {
      state: STATES.ASK_LOCATION,
      profile: { ...session.profile, age },
    });
    return { reply: MESSAGES.askLocation(age), state: session.state };
  }

  if (session.state === STATES.ASK_LOCATION) {
    const department = msg.trim();
    if (department.length < 3) {
      return { reply: '¿En qué departamento vives? (ej: Boyacá, Bogotá, Antioquia...)', state: session.state };
    }
    session = updateSession(sessionId, {
      state: STATES.ASK_FAMILY,
      profile: { ...session.profile, department },
    });
    return { reply: MESSAGES.askFamily(department), state: session.state };
  }

  if (session.state === STATES.ASK_FAMILY) {
    const familySituation = parseFamily(msg);
    session = updateSession(sessionId, {
      state: STATES.ASK_INCOME,
      profile: { ...session.profile, familySituation },
    });
    return { reply: MESSAGES.askIncome(), state: session.state };
  }

  if (session.state === STATES.ASK_INCOME) {
    const canPay = parseIncome(msg);
    session = updateSession(sessionId, {
      state: STATES.ASK_ICFES,
      profile: { ...session.profile, canPay },
    });
    return { reply: MESSAGES.askIcfes(), state: session.state };
  }

  if (session.state === STATES.ASK_ICFES) {
    const icfesScore = parseIcfes(msg);
    const profile = { ...session.profile, icfesScore };

    session = updateSession(sessionId, {
      state: STATES.RESULTS,
      profile,
    });

    const matchedPrograms = matchPrograms(profile);
    const knowledgeContext = buildKnowledgeContext(profile, matchedPrograms);

    try {
      const aiReply = await generateResponse(
        knowledgeContext,
        'Analiza mi perfil y recomiéndame las mejores opciones educativas. Sé específico con los pasos a seguir.',
        session.history,
        matchedPrograms
      );

      updateSession(sessionId, {
        matchedPrograms,
        state: STATES.FOLLOWUP,
        history: [
          ...session.history,
          { role: 'assistant', content: aiReply },
        ],
      });

      return { reply: aiReply, state: STATES.FOLLOWUP, programs: matchedPrograms };
    } catch (err) {
      console.error('AI error:', err.message);
      return { reply: MESSAGES.error(), state: STATES.RESULTS };
    }
  }

  if (session.state === STATES.FOLLOWUP) {
    try {
      const aiReply = await generateFollowup(
        session.profile,
        session.matchedPrograms || [],
        msg,
        session.history
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

  return { reply: MESSAGES.welcome, state: STATES.ASK_AGE };
}

module.exports = { processMessage, MESSAGES };
