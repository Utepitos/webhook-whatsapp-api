const { getSession, updateSession, resetSession, STATES } = require('../src/sessionManager');

let counter = 0;
const uid = () => `test-${counter++}`;

describe('STATES', () => {
  test('exports the expected state constants', () => {
    expect(STATES).toEqual({
      WELCOME: 'WELCOME',
      OPEN_CHAT: 'OPEN_CHAT',
      FOLLOWUP: 'FOLLOWUP',
    });
  });
});

describe('getSession', () => {
  test('creates a fresh WELCOME session for an unknown id', () => {
    const session = getSession(uid());
    expect(session.state).toBe(STATES.WELCOME);
    expect(session.history).toEqual([]);
    expect(typeof session.createdAt).toBe('number');
    expect(typeof session.updatedAt).toBe('number');
  });

  test('returns the same session on repeated calls', () => {
    const id = uid();
    expect(getSession(id)).toEqual(getSession(id));
  });

  test('resets to WELCOME when the TTL has expired', () => {
    const id = uid();
    updateSession(id, { state: STATES.FOLLOWUP });

    jest.spyOn(Date, 'now').mockReturnValue(Date.now() + 31 * 60 * 1000);
    try {
      expect(getSession(id).state).toBe(STATES.WELCOME);
    } finally {
      jest.restoreAllMocks();
    }
  });
});

describe('updateSession', () => {
  test('merges updates and returns the new session', () => {
    const id = uid();
    const updated = updateSession(id, { state: STATES.OPEN_CHAT });
    expect(updated.state).toBe(STATES.OPEN_CHAT);
  });

  test('does not mutate the previously returned reference', () => {
    const id = uid();
    const original = getSession(id);
    updateSession(id, { state: STATES.OPEN_CHAT });
    expect(original.state).toBe(STATES.WELCOME);
  });

  test('updates the updatedAt timestamp on every call', () => {
    const id = uid();
    const { updatedAt: before } = getSession(id);
    const { updatedAt: after } = updateSession(id, { state: STATES.OPEN_CHAT });
    expect(after).toBeGreaterThanOrEqual(before);
  });

  test('persists history correctly', () => {
    const id = uid();
    const history = [{ role: 'user', content: 'hola' }];
    expect(updateSession(id, { history }).history).toEqual(history);
  });
});

describe('resetSession', () => {
  test('returns a fresh WELCOME session and discards previous state', () => {
    const id = uid();
    updateSession(id, { state: STATES.FOLLOWUP, history: [{ role: 'user', content: 'x' }] });
    const fresh = resetSession(id);
    expect(fresh.state).toBe(STATES.WELCOME);
    expect(fresh.history).toEqual([]);
  });
});
