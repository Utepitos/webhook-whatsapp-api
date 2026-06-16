const assert = require('assert');
const {
  buildHistory,
  buildPredictionBody,
  normalizePredictionResponse,
} = require('../src/flowiseClient');

const history = buildHistory([
  { role: 'user', content: 'Hola' },
  { role: 'assistant', content: 'Hola, ¿en qué te ayudo?' },
]);

assert.deepStrictEqual(history, [
  { role: 'userMessage', content: 'Hola' },
  { role: 'apiMessage', content: 'Hola, ¿en qué te ayudo?' },
]);

const body = buildPredictionBody({
  question: 'Tengo 17 años y vivo en Boyacá',
  knowledgeContext: 'contexto',
  history: [{ role: 'assistant', content: 'previo' }],
  matches: [{ id: 'sena_tecnica', nombre: 'SENA' }],
  profile: { age: 17, department: 'Boyacá' },
  sessionId: 'demo-1',
});

assert.strictEqual(body.question, 'Tengo 17 años y vivo en Boyacá');
assert.strictEqual(body.streaming, false);
assert.strictEqual(body.overrideConfig.sessionId, 'demo-1');
assert.strictEqual(body.overrideConfig.vars.knowledgeContext, 'contexto');
assert.ok(body.overrideConfig.vars.matches.includes('sena_tecnica'));

assert.strictEqual(normalizePredictionResponse({ text: '  Hola mundo  ' }), 'Hola mundo');
assert.strictEqual(normalizePredictionResponse({ result: 'respuesta' }), 'respuesta');
assert.strictEqual(normalizePredictionResponse({ output: 'salida' }), 'salida');
assert.strictEqual(normalizePredictionResponse({}), '');

console.log('Smoke test OK');