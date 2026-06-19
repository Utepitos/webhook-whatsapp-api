const assert = require('assert');
const http = require('http');

async function main() {
  const captured = [];

  const server = http.createServer((req, res) => {
    let body = '';

    req.on('data', (chunk) => {
      body += chunk;
    });

    req.on('end', () => {
      captured.push({
        method: req.method,
        url: req.url,
        headers: req.headers,
        body: body ? JSON.parse(body) : {},
      });

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ text: 'Respuesta simulada de n8n' }));
    });
  });

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  process.env.N8N_WEBHOOK_URL = `http://127.0.0.1:${port}`;
  process.env.N8N_API_KEY = 'demo-key';

  const { resetSession } = require('../src/sessionManager');
  const { processMessage } = require('../src/conversationFlow');

  const sessionId = 'smoke-session';
  resetSession(sessionId);

  const first = await processMessage(sessionId, 'Hola');
  assert.strictEqual(first.state, 'OPEN_CHAT');
  assert.ok(first.reply.includes('EduRoute AI'));

  const second = await processMessage(sessionId, 'Tengo 17 años, vivo en Boyacá y no puedo pagar universidad. Saqué 340 en el ICFES.');
  assert.strictEqual(second.state, 'FOLLOWUP');
  assert.strictEqual(second.reply, 'Respuesta simulada de n8n');
  assert.strictEqual(captured.length, 1);
  assert.strictEqual(captured[0].method, 'POST');
  assert.strictEqual(captured[0].url, '/');
  assert.strictEqual(captured[0].body.question, 'Tengo 17 años, vivo en Boyacá y no puedo pagar universidad. Saqué 340 en el ICFES.');
  assert.deepStrictEqual(captured[0].body.history, [
    { role: 'assistant', content: '¡Hola! Soy *EduRoute AI* 🎓\n\nCuéntame tu situación con libertad y te orientaré.' },
  ]);
  assert.strictEqual(captured[0].body.sessionId, sessionId);

  server.close();
  console.log('Conversation smoke test OK');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
