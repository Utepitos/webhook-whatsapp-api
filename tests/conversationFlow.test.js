jest.mock('../src/flowiseClient');
const { runPrediction } = require('../src/flowiseClient');
const { processMessage, MESSAGES } = require('../src/conversationFlow');
const { resetSession, STATES } = require('../src/sessionManager');

let counter = 0;
const uid = () => `flow-test-${counter++}`;

beforeEach(() => {
  jest.clearAllMocks();
});

describe('MESSAGES', () => {
  test('are plain strings, not functions', () => {
    expect(typeof MESSAGES.welcome).toBe('string');
    expect(typeof MESSAGES.error).toBe('string');
    expect(typeof MESSAGES.reset).toBe('string');
  });
});

describe('processMessage — reset commands', () => {
  test.each(['reiniciar', 'REINICIAR', 'reset', 'RESET'])(
    '"%s" resets the session and returns the reset message',
    async (cmd) => {
      const id = uid();
      runPrediction.mockResolvedValue('respuesta ai');
      await processMessage(id, 'hola');
      await processMessage(id, 'tengo 17 años');

      const result = await processMessage(id, cmd);
      expect(result.state).toBe(STATES.WELCOME);
      expect(result.reply).toBe(MESSAGES.reset);
    }
  );
});

describe('processMessage — WELCOME state', () => {
  test('returns the welcome message without calling AI', async () => {
    const id = uid();
    const result = await processMessage(id, 'hola');
    expect(result.reply).toBe(MESSAGES.welcome);
    expect(result.state).toBe(STATES.OPEN_CHAT);
    expect(runPrediction).not.toHaveBeenCalled();
  });

  test('transitions to OPEN_CHAT regardless of the message content', async () => {
    const id = uid();
    const result = await processMessage(id, 'cualquier texto');
    expect(result.state).toBe(STATES.OPEN_CHAT);
  });
});

describe('processMessage — active states (OPEN_CHAT and FOLLOWUP)', () => {
  let sessionId;

  beforeEach(async () => {
    sessionId = uid();
    await processMessage(sessionId, 'hola'); // advance past WELCOME
  });

  test('calls the AI with the user message and sessionId', async () => {
    runPrediction.mockResolvedValue('Tu orientación es...');
    await processMessage(sessionId, 'Tengo 17 años, vivo en Boyacá');

    expect(runPrediction).toHaveBeenCalledWith(
      expect.objectContaining({
        question: 'Tengo 17 años, vivo en Boyacá',
        sessionId,
      })
    );
  });

  test('returns the AI reply and transitions to FOLLOWUP', async () => {
    runPrediction.mockResolvedValue('Puedes aplicar a Ser Pilo Paga');
    const result = await processMessage(sessionId, 'mi pregunta');
    expect(result.reply).toBe('Puedes aplicar a Ser Pilo Paga');
    expect(result.state).toBe(STATES.FOLLOWUP);
  });

  test('saves the user message in history so subsequent AI calls have correct context', async () => {
    runPrediction.mockResolvedValue('primera respuesta');
    await processMessage(sessionId, 'primer mensaje');

    runPrediction.mockResolvedValue('segunda respuesta');
    await processMessage(sessionId, 'segunda pregunta');

    const historyPassedOnSecondCall = runPrediction.mock.calls[1][0].history;
    expect(historyPassedOnSecondCall).toEqual(
      expect.arrayContaining([{ role: 'user', content: 'primer mensaje' }])
    );
  });

  test('returns the error message and preserves the current state when AI throws', async () => {
    runPrediction.mockRejectedValue(new Error('Flowise unavailable'));
    const result = await processMessage(sessionId, 'pregunta');
    expect(result.reply).toBe(MESSAGES.error);
    expect(result.state).toBe(STATES.OPEN_CHAT);
  });

  test('trims whitespace from the user message before processing', async () => {
    runPrediction.mockResolvedValue('ok');
    await processMessage(sessionId, '  mensaje con espacios  ');
    expect(runPrediction).toHaveBeenCalledWith(
      expect.objectContaining({ question: 'mensaje con espacios' })
    );
  });
});
