# Tara AI

Tara AI is a WhatsApp-based conversational assistant that helps young people in Colombia navigate higher-education opportunities. Instead of searching across multiple websites and confusing forms, students can ask questions directly in WhatsApp and receive clear, personalized guidance about programs, admission requirements, documents, and next steps.

---

## Project Overview

Access to higher education in Colombia is blocked not only by cost, but also by a lack of clear, accessible information — especially for students in rural or low-income contexts. Tara AI addresses this directly: it meets students where they already are (WhatsApp) and turns a complex, fragmented process into a single guided conversation.

The assistant can answer questions such as:

- "I am 18 and I live in Boyacá. What options do I have?"
- "I cannot afford private university. What free programs are available?"
- "What documents do I need to apply?"
- "I already have an ICFES score. What can I do with it?"

---

## How the AI Solution Works — Technical Breakdown

### Architecture

```
WhatsApp User
      │
      ▼
Meta Cloud API  ──►  Express Webhook (app.js)
                            │
                    Signature Verification
                    (HMAC-SHA256)
                            │
                    conversationFlow.js
                    (State machine + history)
                            │
                    flowiseClient.js
                    (REST call to Flowise)
                            │
                    Flowise AI Flow
                    (LLM + prompt + knowledge)
                            │
                    ◄─────────────────────────
                    whatsappClient.js
                    (Meta Graph API v19.0)
                            │
                            ▼
              WhatsApp User receives reply
```

### Components

#### 1. Webhook server (`app.js`)
The entry point is an Express HTTP server that exposes three routes:

- `GET /webhook` — used by Meta to verify the webhook subscription using a `hub.verify_token` challenge.
- `POST /webhook` — receives all incoming WhatsApp events. Every request is authenticated with HMAC-SHA256 signature validation (`x-hub-signature-256`) before any processing occurs. Once validated, the server responds `200 OK` immediately (so Meta does not retry) and processes the message asynchronously.
- `GET /health` — lightweight health check endpoint for uptime monitoring.

#### 2. Conversation state machine (`src/conversationFlow.js`)
Each user phone number acts as a session identifier. The conversation progresses through three states:

| State | Description |
|---|---|
| `WELCOME` | First contact — bot sends greeting and transitions to `OPEN_CHAT` |
| `OPEN_CHAT` | Active conversation — all messages are forwarded to the AI engine |
| `FOLLOWUP` | Subsequent turns with full conversation history attached |

The user can type `reiniciar` or `reset` at any time to clear their session and start over.

#### 3. Session manager (`src/sessionManager.js`)
Sessions are stored in-process using a `Map` keyed by phone number (`from`). Each session holds:

- Current state (`WELCOME`, `OPEN_CHAT`, `FOLLOWUP`)
- Full conversation history (array of `{ role, content }` objects)
- Creation and last-update timestamps

Sessions expire automatically after **30 minutes of inactivity** (`SESSION_TTL_MS = 30 * 60 * 1000`). Expired sessions are reset to `WELCOME` on next contact.

#### 4. Flowise client (`src/flowiseClient.js`)
This module is the bridge between the bot and the AI engine. It:

1. Builds a prediction request payload with the current user message, full conversation history (mapped to Flowise's `userMessage` / `apiMessage` roles), and the session ID for context persistence on the Flowise side.
2. POSTs to `{FLOWISE_URL}/api/v1/prediction/{FLOWISE_FLOW_ID}` with optional Bearer token authentication.
3. Applies a configurable timeout (`FLOWISE_TIMEOUT_MS`, default 30 seconds).
4. Normalizes the response by checking multiple possible field names (`text`, `result`, `output`, `answer`, `message`, `response`, and nested `outputs[0]`), making the client resilient to changes in the Flowise response schema.

#### 5. WhatsApp client (`src/whatsappClient.js`)
Handles two responsibilities:

- **`extractMessage(body)`** — parses the raw Meta webhook payload and returns a normalized `{ from, text, type, messageId }` object. Returns `null` for non-text events (images, audio, etc.), which the bot silently ignores.
- **`sendMessage(to, text)`** — POSTs to the Meta Graph API v19.0 (`/messages` endpoint) with the bot's reply. Includes detailed HTTP error logging for debugging. Operates in a demo mode (logs to console only) if credentials are not configured.

### Data flow per message (detailed)

1. User sends a WhatsApp text message.
2. Meta forwards the event to `POST /webhook` via HTTPS.
3. The server verifies the HMAC-SHA256 signature against `WHATSAPP_APP_SECRET`.
4. `extractMessage()` parses the payload and returns the sender's phone number and message text.
5. `processMessage()` looks up or creates the in-memory session for that phone number.
6. If it is the user's first message, the welcome response is returned without calling the AI.
7. On subsequent messages, the full conversation history plus the new message are sent to Flowise.
8. Flowise runs the configured AI flow (LLM + retrieval + system prompt) and returns a response.
9. The response is appended to the session history and sent back to the user via the Meta Graph API.
10. The session's `updatedAt` timestamp is refreshed.

---

## Tools, Platforms, and Data Sources

| Layer | Technology |
|---|---|
| Runtime | Node.js 18+ |
| Web framework | Express 4 |
| Messaging channel | WhatsApp Cloud API (Meta Graph API v19.0) |
| AI orchestration | Flowise (self-hosted or cloud) |
| HTTP client | Axios |
| Deployment | Render |
| Testing | Jest + Supertest |
| Development | Nodemon |

**Data sources used by the AI flow (configured inside Flowise):**

- Public information from Colombian higher-education institutions (ICETEX, MEN, SENA, public universities).
- Official ICFES score interpretation guidelines.
- Scholarship and financial aid program documentation.

No personal student data is stored beyond the active session window (30 minutes). Conversation history exists only in server memory and is never written to disk or a database.

---

## Responsible AI Statement

### Risk identified: Incorrect or incomplete educational guidance

The AI model may produce responses that are outdated, incomplete, or contextually inaccurate — for example, citing a program that has changed its admission requirements, or omitting a relevant scholarship. In the Colombian education context, acting on incorrect information could lead a student to miss an application deadline or a funding opportunity.

**How the design mitigates this risk:**

- Every response ends with a prompt for the user to verify details directly with the institution or call a counselor, keeping the bot explicitly positioned as a first-step guide, not a final authority.
- The Flowise flow is built around a curated, version-controlled knowledge base rather than open-ended web retrieval, reducing hallucination risk.
- The system prompt instructs the model to express uncertainty explicitly when information may be incomplete, rather than generating a confident but potentially wrong answer.
- Session timeouts (30 minutes) prevent the bot from acting on stale context across days or sessions.

### Where human judgment remains central

EduRoute AI is designed to be a first point of contact, not a replacement for human advisors. Human judgment remains essential at every decision point that matters:

- **Final application decisions** — the bot provides orientation; students must verify requirements and submit documents themselves through official institutional channels.
- **Financial aid assessment** — eligibility for ICETEX loans, SENA programs, or local scholarships involves individual socioeconomic documentation that only a human counselor can evaluate properly.
- **Edge cases and personal circumstances** — students with disabilities, adult learners returning to education, or students with non-standard academic backgrounds need personalized advice that goes beyond what a general-purpose assistant can reliably provide.
- **Verification of AI output** — any specific data the bot provides (deadlines, scores, quotas) should be confirmed directly with the institution before the student acts on it.

The bot is designed to reduce friction and lower the barrier to starting the process — not to replace the human systems that guide students through it.

---

## Demo

A 3–5 minute video walkthrough of the solution, covering its purpose, technical architecture, and a live conversation demo, is included as a separate deliverable alongside this repository.

---

## Current Status

The bot is connected to WhatsApp and can receive and reply to real messages in production. The webhook is deployed on Render and registered with Meta's WhatsApp Cloud API.

---

## Running Locally

```bash
# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Fill in WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_APP_SECRET,
# VERIFY_TOKEN, FLOWISE_URL, FLOWISE_FLOW_ID, FLOWISE_API_KEY

# Start development server
npm run dev

# Run tests
npm test

# Run with coverage
npm run test:coverage
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `WHATSAPP_TOKEN` | Meta permanent access token |
| `WHATSAPP_PHONE_ID` | WhatsApp Business phone number ID |
| `WHATSAPP_APP_SECRET` | App secret for webhook signature validation |
| `VERIFY_TOKEN` | Custom token for webhook verification challenge |
| `FLOWISE_URL` | Base URL of the Flowise instance |
| `FLOWISE_FLOW_ID` | ID of the Flowise chatflow to invoke |
| `FLOWISE_API_KEY` | Optional API key for authenticated Flowise instances |
| `FLOWISE_TIMEOUT_MS` | Request timeout in milliseconds (default: 30000) |
| `PORT` | HTTP port (default: 3000) |
