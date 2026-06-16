const { runPrediction, hasFlowiseConfig } = require('./flowiseClient');

function fallbackResponse(matches) {
  if (!matches || matches.length === 0) {
    return `Según tu perfil, te recomiendo comenzar con el *SENA* ya que es completamente gratuito y no requiere puntaje ICFES específico.\n\nEscribe "reiniciar" para empezar de nuevo o visita sofiaplus.edu.co para más información.`;
  }

  const top = matches.slice(0, 4);
  let text = `Entiendo tu situación. Según tu perfil encontré *${matches.length} opciones* para ti:\n\n`;

  top.forEach((p, i) => {
    text += `*OPCIÓN ${i + 1}: ${p.nombre}*\n`;
    text += `✅ Costo: ${p.costo}\n`;
    text += `🏛 Entidad: ${p.entidad}\n`;
    if (p.programas_ejemplo?.length) {
      text += `📚 Ejemplos: ${p.programas_ejemplo.slice(0, 3).join(', ')}\n`;
    }
    text += `📞 Contacto: ${p.contacto}\n\n`;
  });

  const allDocs = [...new Set(top.flatMap((p) => p.documentos))].slice(0, 6);
  text += `*DOCUMENTOS QUE VAS A NECESITAR:*\n`;
  allDocs.forEach((d) => { text += `• ${d}\n`; });

  text += `\n*TUS PRÓXIMOS PASOS:*\n`;
  const firstProgram = top[0];
  firstProgram.pasos.slice(0, 4).forEach((s, i) => { text += `${i + 1}. ${s}\n`; });

  text += `\n_Tu situación tiene solución. Miles de jóvenes en Colombia han accedido a estas oportunidades. ¡Tú también puedes! 💪_\n\n_Puedes preguntarme cualquier duda sobre estos programas._`;

  return text;
}

function fallbackFollowup(userQuestion) {
  return `Para resolver tu duda sobre "${userQuestion}", te recomiendo contactar directamente a las entidades mencionadas:\n\n• *SENA:* sofiaplus.edu.co | 018000910270\n• *ICETEX:* icetex.gov.co | 018000912227\n• *Generación E:* generacione.mineducacion.gov.co\n• *UPTC (Boyacá):* uptc.edu.co\n\n_Escribe "reiniciar" para hacer una nueva consulta._`;
}

const SYSTEM_PROMPT = `Eres EduRuta AI, un orientador educativo cálido y empático que ayuda a jóvenes colombianos de bajos recursos a encontrar oportunidades de educación superior.

Tu objetivo es analizar el perfil del estudiante y presentar las mejores opciones educativas disponibles de forma clara, ordenada y motivadora.

REGLAS:
- Sé empático y alentador. Muchos usuarios vienen sin esperanza.
- Usa lenguaje sencillo y cercano (tuteo colombiano).
- Sé específico con los programas: nombres reales, entidades reales, pasos concretos.
- Prioriza las opciones más relevantes para su perfil (departamento, puntaje, situación económica).
- Siempre incluye: qué pueden estudiar, documentos necesarios y próximos pasos numerados.
- No inventes programas. Solo usa los que te proveo en el contexto.
- Termina con un mensaje motivador breve.

FORMATO DE RESPUESTA PARA RESULTADOS:
Usa este formato claro:

Entiendo tu situación. Según tu perfil encontré [N] opciones para ti:

OPCIÓN 1: [Nombre del programa]
✅ Costo: [costo]
📋 Requisitos: [requisitos clave]

OPCIÓN 2: ...

DOCUMENTOS QUE VAS A NECESITAR:
• [documento 1]
• [documento 2]

TUS PRÓXIMOS PASOS:
1. [paso concreto]
2. [paso concreto]
3. [paso concreto]

[Mensaje motivador]`;

async function generateResponse(knowledgeContext, userMessage, history = [], matches = [], profile = {}, sessionId = null) {
  if (hasFlowiseConfig()) {
    try {
      return await runPrediction({
        question: userMessage,
        knowledgeContext,
        history,
        matches,
        profile,
        sessionId,
      });
    } catch (err) {
      console.error('[Flowise] Error ejecutando predicción:', err.message);
      // If Flowise fails, fall back to deterministic local response
      return fallbackResponse(matches);
    }
  }

  // No Flowise configured: use deterministic fallback
  return fallbackResponse(matches);
}

async function generateFollowup(profile, matchedPrograms, userQuestion, history = [], sessionId = null) {
  if (hasFlowiseConfig()) {
    try {
      return await runPrediction({
        question: userQuestion,
        knowledgeContext: `Seguimiento sobre orientación educativa. Perfil: ${JSON.stringify(profile)}`,
        history,
        matches: matchedPrograms,
        profile,
        sessionId,
      });
    } catch (err) {
      console.error('[Flowise] Error ejecutando seguimiento:', err.message);
      return fallbackFollowup(userQuestion);
    }
  }

  return fallbackFollowup(userQuestion);
}

module.exports = { generateResponse, generateFollowup };
