const request = require('supertest');
const crypto = require('crypto');

jest.mock('../src/conversationFlow', () => ({
  processMessage: jest.fn().mockResolvedValue({ reply: 'respuesta test', state: 'FOLLOWUP' }),
}));

jest.mock('../src/whatsappClient', () => ({
  sendMessage: jest.fn().mockResolvedValue(),
  extractMessage: jest.requireActual('../src/whatsappClient').extractMessage,
}));

const app = require('../app');
const { processMessage } = require('../src/conversationFlow');
const { sendMessage } = require('../src/whatsappClient');

const TEST_SECRET = 'test-app-secret';
const TEST_VERIFY_TOKEN = 'test-verify-token';

const textMessagePayload = {
  entry: [{
    changes: [{
      value: {
        messages: [{
          from: '573001234567',
          id: 'wamid.abc',
          type: 'text',
          text: { body: 'Hola' },
        }],
      },
    }],
  }],
};

function signPayload(body, secret) {
  const raw = typeof body === 'string' ? body : JSON.stringify(body);
  return `sha256=${crypto.createHmac('sha256', secret).update(raw).digest('hex')}`;
}

beforeEach(() => {
  jest.clearAllMocks();
  process.env.VERIFY_TOKEN = TEST_VERIFY_TOKEN;
});

describe('GET /webhook — Meta verification', () => {
  test('returns 200 and echoes the challenge when the token matches', async () => {
    await request(app)
      .get('/webhook')
      .query({ 'hub.mode': 'subscribe', 'hub.challenge': 'ch_abc123', 'hub.verify_token': TEST_VERIFY_TOKEN })
      .expect(200)
      .expect('ch_abc123');
  });

  test('returns 403 when the verify token does not match', async () => {
    await request(app)
      .get('/webhook')
      .query({ 'hub.mode': 'subscribe', 'hub.challenge': 'ch_abc123', 'hub.verify_token': 'wrong-token' })
      .expect(403);
  });

  test('returns 403 when hub.mode is not subscribe', async () => {
    await request(app)
      .get('/webhook')
      .query({ 'hub.mode': 'unsubscribe', 'hub.challenge': 'ch_abc123', 'hub.verify_token': TEST_VERIFY_TOKEN })
      .expect(403);
  });
});

describe('POST /webhook — signature validation', () => {
  beforeEach(() => {
    process.env.WHATSAPP_APP_SECRET = TEST_SECRET;
  });

  afterEach(() => {
    delete process.env.WHATSAPP_APP_SECRET;
  });

  test('returns 401 when the signature header is missing', async () => {
    await request(app)
      .post('/webhook')
      .send(textMessagePayload)
      .expect(401);
  });

  test('returns 401 when the signature does not match the payload', async () => {
    await request(app)
      .post('/webhook')
      .set('x-hub-signature-256', 'sha256=invalidsignature00000000000000000000000000000000000000000000000000')
      .send(textMessagePayload)
      .expect(401);
  });

  test('returns 200 when the signature is valid', async () => {
    const raw = JSON.stringify(textMessagePayload);
    await request(app)
      .post('/webhook')
      .set('x-hub-signature-256', signPayload(raw, TEST_SECRET))
      .set('Content-Type', 'application/json')
      .send(raw)
      .expect(200);
  });
});

describe('POST /webhook — message processing', () => {
  beforeEach(() => {
    delete process.env.WHATSAPP_APP_SECRET; // dev mode: skip signature check
  });

  test('responds 200 immediately and then calls processMessage and sendMessage', async () => {
    await request(app).post('/webhook').send(textMessagePayload).expect(200);
    await new Promise((resolve) => setImmediate(resolve));

    expect(processMessage).toHaveBeenCalledWith('573001234567', 'Hola');
    expect(sendMessage).toHaveBeenCalledWith('573001234567', 'respuesta test');
  });

  test('responds 200 and does not call processMessage for non-text message types', async () => {
    const payload = JSON.parse(JSON.stringify(textMessagePayload));
    payload.entry[0].changes[0].value.messages[0].type = 'image';

    await request(app).post('/webhook').send(payload).expect(200);
    await new Promise((resolve) => setImmediate(resolve));

    expect(processMessage).not.toHaveBeenCalled();
  });

  test('responds 200 even when processMessage throws an unexpected error', async () => {
    processMessage.mockRejectedValueOnce(new Error('crash inesperado'));
    await request(app).post('/webhook').send(textMessagePayload).expect(200);
  });
});

describe('GET /health', () => {
  test('returns { status: "ok" }', async () => {
    await request(app).get('/health').expect(200).expect({ status: 'ok' });
  });
});

describe('GET /', () => {
  test('returns service info', async () => {
    const { body } = await request(app).get('/').expect(200);
    expect(body.service).toBe('EduRoute AI');
    expect(body.status).toBe('running');
  });
});
