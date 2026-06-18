const SESSION_TTL_MS = 30 * 60 * 1000;

const sessions = new Map();

const STATES = {
  WELCOME: 'WELCOME',
  OPEN_CHAT: 'OPEN_CHAT',
  FOLLOWUP: 'FOLLOWUP',
};

function createSession(sessionId) {
  const now = Date.now();
  return { id: sessionId, state: STATES.WELCOME, history: [], createdAt: now, updatedAt: now };
}

function isExpired(session) {
  return Date.now() - session.updatedAt > SESSION_TTL_MS;
}

function getSession(sessionId) {
  const existing = sessions.get(sessionId);
  if (!existing || isExpired(existing)) {
    const fresh = createSession(sessionId);
    sessions.set(sessionId, fresh);
    return fresh;
  }
  return existing;
}

function updateSession(sessionId, updates) {
  const session = getSession(sessionId);
  const updated = { ...session, ...updates, updatedAt: Date.now() };
  sessions.set(sessionId, updated);
  return updated;
}

function resetSession(sessionId) {
  sessions.delete(sessionId);
  return getSession(sessionId);
}

module.exports = { getSession, updateSession, resetSession, STATES };
