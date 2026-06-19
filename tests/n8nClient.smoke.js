const assert = require('assert');
const {
  buildHistory,
  buildWebhookBody,
  normalizeN8nResponse,
} = require('../src/n8nClient');

const history = buildHistory([
  { role: 'user', content: 'Hola' },
  { role: 'assistant', content: 'Hola, ¿en qué te ayudo?' },
]);

assert.deepStrictEqual(history, [
  { role: 'user', content: 'Hola' },
  { role: 'assistant', content: 'Hola, ¿en qué te ayudo?' },
]);

const body = buildWebhookBody({
  question: 'Tengo 17 años y vivo en Boyacá',
  history: [{ role: 'assistant', content: 'previo' }],
  sessionId: 'demo-1',
});

assert.strictEqual(body.question, 'Tengo 17 años y vivo en Boyacá');
assert.deepStrictEqual(body.history, [
  { role: 'assistant', content: 'previo' },
]);
assert.strictEqual(body.sessionId, 'demo-1');

assert.strictEqual(normalizeN8nResponse({ text: '  Hola mundo  ' }), 'Hola mundo');
assert.strictEqual(normalizeN8nResponse({ result: 'respuesta' }), 'respuesta');
assert.strictEqual(normalizeN8nResponse({ output: 'salida' }), 'salida');
assert.strictEqual(normalizeN8nResponse({ body: { message: 'ok' } }), 'ok');
assert.strictEqual(normalizeN8nResponse({}), '');

console.log('Smoke test OK');
