const http = require('http');
const {
  buildHistory,
  buildPredictionBody,
  normalizePredictionResponse,
  runPrediction,
} = require('../src/flowiseClient');

describe('buildHistory', () => {
  test('maps roles to Flowise format', () => {
    expect(buildHistory([
      { role: 'user', content: 'Hola' },
      { role: 'assistant', content: '¿En qué te ayudo?' },
    ])).toEqual([
      { role: 'userMessage', content: 'Hola' },
      { role: 'apiMessage', content: '¿En qué te ayudo?' },
    ]);
  });

  test('filters out items missing role or content', () => {
    const result = buildHistory([
      { role: 'user', content: 'válido' },
      { content: 'sin rol' },
      { role: 'assistant' },
      null,
    ]);
    expect(result).toHaveLength(1);
    expect(result[0].content).toBe('válido');
  });

  test('coerces content to string', () => {
    expect(buildHistory([{ role: 'user', content: 42 }])[0].content).toBe('42');
  });

  test('returns empty array for empty input', () => {
    expect(buildHistory([])).toEqual([]);
  });
});

describe('buildPredictionBody', () => {
  test('builds a correctly structured body', () => {
    const body = buildPredictionBody({ question: '¿Cuál es mi opción?', sessionId: 'sess-1' });
    expect(body.question).toBe('¿Cuál es mi opción?');
    expect(body.streaming).toBe(false);
    expect(body.overrideConfig).toEqual({ sessionId: 'sess-1' });
  });

  test('includes an empty history array when none is provided', () => {
    expect(buildPredictionBody({ question: 'q', sessionId: null }).history).toEqual([]);
  });
});

describe('normalizePredictionResponse', () => {
  test.each([
    [{ text: '  Respuesta  ' }, 'Respuesta'],
    [{ result: 'resultado' }, 'resultado'],
    [{ output: 'salida' }, 'salida'],
    [{ answer: 'respuesta' }, 'respuesta'],
    [{ message: 'mensaje' }, 'mensaje'],
    [{ response: 'response' }, 'response'],
  ])('extracts the text field from %o', (input, expected) => {
    expect(normalizePredictionResponse(input)).toBe(expected);
  });

  test('extracts text from a nested outputs array', () => {
    expect(normalizePredictionResponse({ outputs: [{ text: 'anidado' }] })).toBe('anidado');
  });

  test('returns empty string for an unrecognized structure', () => {
    expect(normalizePredictionResponse({})).toBe('');
  });

  test('returns empty string for null input', () => {
    expect(normalizePredictionResponse(null)).toBe('');
  });
});

describe('runPrediction', () => {
  let server;

  beforeAll(async () => {
    server = http.createServer((_req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ text: 'Respuesta de Flowise' }));
    });
    await new Promise((resolve) => server.listen(0, resolve));
    const { port } = server.address();
    process.env.FLOWISE_URL = `http://127.0.0.1:${port}`;
    process.env.FLOWISE_FLOW_ID = 'test-flow';
    process.env.FLOWISE_API_KEY = 'test-key';
  });

  afterAll(() => server.close());

  test('returns the text from a successful Flowise response', async () => {
    await expect(runPrediction({ question: '¿Y si no paso?', sessionId: 'u1' }))
      .resolves.toBe('Respuesta de Flowise');
  });

  test('throws when Flowise URL is not configured', async () => {
    const saved = process.env.FLOWISE_URL;
    delete process.env.FLOWISE_URL;
    await expect(runPrediction({ question: 'x', sessionId: 'u1' })).rejects.toThrow();
    process.env.FLOWISE_URL = saved;
  });

  test('throws when Flowise returns no usable text field', async () => {
    server.removeAllListeners('request');
    server.on('request', (_req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ unexpected: 'shape' }));
    });
    await expect(runPrediction({ question: 'x', sessionId: 'u1' })).rejects.toThrow(
      'Flowise no devolvió un campo de texto utilizable'
    );
  });
});
