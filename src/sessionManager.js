const sessions = new Map();

const STATES = {
  WELCOME: 'WELCOME',
  OPEN_CHAT: 'OPEN_CHAT',
  FOLLOWUP: 'FOLLOWUP',
};

function getSession(sessionId) {
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, {
      id: sessionId,
      state: STATES.WELCOME,
      history: [],
      createdAt: Date.now(),
    });
  }
  return sessions.get(sessionId);
}

function updateSession(sessionId, updates) {
  const session = getSession(sessionId);
  Object.assign(session, updates);
  sessions.set(sessionId, session);
  return session;
}

function resetSession(sessionId) {
  sessions.delete(sessionId);
  return getSession(sessionId);
}

module.exports = { getSession, updateSession, resetSession, STATES };
