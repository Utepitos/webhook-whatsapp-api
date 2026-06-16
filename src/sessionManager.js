const sessions = new Map();

const STATES = {
  WELCOME: 'WELCOME',
  OPEN_CHAT: 'OPEN_CHAT',
  ASK_AGE: 'ASK_AGE',
  ASK_LOCATION: 'ASK_LOCATION',
  ASK_FAMILY: 'ASK_FAMILY',
  ASK_INCOME: 'ASK_INCOME',
  ASK_ICFES: 'ASK_ICFES',
  RESULTS: 'RESULTS',
  FOLLOWUP: 'FOLLOWUP',
};

function getSession(sessionId) {
  if (!sessions.has(sessionId)) {
    sessions.set(sessionId, {
      id: sessionId,
      state: STATES.WELCOME,
      profile: {},
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
