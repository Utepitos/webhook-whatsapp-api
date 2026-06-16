const { getSession, updateSession, STATES } = require('./sessionManager');
const { matchPrograms, buildKnowledgeContext } = require('./knowledgeBase');
const { generateResponse, generateFollowup } = require('./aiClient');

const MESSAGES = {
  welcome: `¡Hola! Soy *EduRuta AI* 🎓

Te ayudo a encontrar oportunidades de educación superior gratuitas o de bajo costo en Colombia.

Cuéntame tu situación con libertad para entender tu caso y orientarte mejor.

Puedes incluir edad, departamento, situación familiar, si puedes pagar universidad, puntaje ICFES y cualquier otro detalle útil.`,

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
    `Listo, empecemos de nuevo.\n\n¡Hola! Soy *EduRuta AI* 🎓\nCuéntame tu situación con libertad.`,
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

function extractHints(input) {
  const text = input.trim().toLowerCase();
  const profile = {};

  const ageMatch = text.match(/\b(1[2-9]|[2-5][0-9]|60)\b/);
  if (ageMatch && (text.includes('año') || text.includes('edad') || text.includes('tengo'))) {
    profile.age = parseInt(ageMatch[1], 10);
  }

  const icfesMatch = text.match(/\b([0-9]{2,3})\b/);
  if ((text.includes('icfes') || text.includes('saber 11') || text.includes('puntaje')) && icfesMatch) {
    profile.icfesScore = String(parseInt(icfesMatch[1], 10));
  }

  if (text.includes('boyac')) profile.department = 'Boyacá';
  else if (text.includes('bogot')) profile.department = 'Bogotá';
  else if (text.includes('antioqu')) profile.department = 'Antioquia';
  else if (text.includes('cundinamarc')) profile.department = 'Cundinamarca';
  else if (text.includes('casanar')) profile.department = 'Casanare';
  else if (text.includes('arauca')) profile.department = 'Arauca';

  if (text.includes('cabeza de hogar') || text.includes('madre sola') || text.includes('padre solo')) {
    profile.familySituation = 'cabeza_hogar';
  } else if (text.includes('estrato 1') || text.includes('estrato 2') || text.includes('bajos recursos') || text.includes('sin recursos')) {
    profile.familySituation = 'bajo_recursos';
  } else if (text.includes('estrato 3') || text.includes('recursos medios')) {
    profile.familySituation = 'recursos_medios';
  } else if (text.includes('caja de compensacion') || text.includes('caja compensacion') || text.includes('empleado formal')) {
    profile.familySituation = 'empleado_formal';
  }

  if (text.includes('no puedo pagar') || text.includes('no podemos pagar') || text.includes('sin recursos') || text.includes('no hay dinero')) {
    profile.canPay = 'no';
  } else if (text.includes('podemos pagar algo') || text.includes('parcial') || text.includes('algo')) {
    profile.canPay = 'partial';
  } else if (text.includes('si puedo pagar') || text.includes('sí puedo pagar') || text.includes('podemos costear')) {
    profile.canPay = 'yes';
  }

  return profile;
}

async function processMessage(sessionId, userMessage) {
  const msg = userMessage.trim();

  if (msg.toLowerCase() === 'reiniciar' || msg.toLowerCase() === 'reset') {
    const { resetSession } = require('./sessionManager');
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
    const profilePatch = extractHints(msg);
    const profile = { ...session.profile, ...profilePatch };
    const matchedPrograms = matchPrograms(profile);
    const knowledgeContext = buildKnowledgeContext(profile, matchedPrograms);

    try {
      const aiReply = await generateResponse(
        knowledgeContext,
        msg,
        session.history,
        matchedPrograms,
        profile,
        sessionId
      );

      updateSession(sessionId, {
        profile,
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
      return { reply: MESSAGES.error(), state: STATES.OPEN_CHAT };
    }
  }

  if (session.state === STATES.FOLLOWUP) {
    try {
      const aiReply = await generateFollowup(
        session.profile,
        session.matchedPrograms || [],
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
