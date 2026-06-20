# Responsible AI Statement — Tara (EduRoute AI)

Tara is a WhatsApp assistant that helps people in vulnerable situations in Colombia
understand and access **free** state social programs, public health coverage, and
free/low-cost education pathways (SISBEN, Familias en Acción, Colombia Mayor, Jóvenes
en Acción, SENA, Generación E, free legal clinics, and more).

Because our users are often low-income, low-digital-literacy, and sometimes minors or
people in crisis, responsible design is not a feature for us — it is the core of the
product. This document states our system honestly: what it does, the realistic risks it
carries, and how the design mitigates them.

---

## 1. How the AI actually works (full disclosure)

We disclose every tool, model, and data source used, as required:

| Layer | What we use |
|-------|-------------|
| Channel | WhatsApp Cloud API (Meta) |
| Backend | Node.js + Express on Render (webhook relay) |
| Orchestration | n8n — LangChain **AI Agent** node |
| Model | **Groq**, model `openai/gpt-oss-120b` (open-weight, free tier) |
| Memory | n8n buffer-window memory + per-session history keyed by an opaque WhatsApp ID |
| Knowledge | A **curated, source-cited knowledge base written into the system prompt** (official Colombian government programs). Every program lists its responsible entity, official website, and/or toll-free line. |

**Important honesty note:** the knowledge base is hand-curated inside the prompt, not
retrieved live from a database. This is a deliberate, auditable choice for the hackathon
build window: a small, verified, human-written set of facts is *safer* than an
ungrounded model improvising. The trade-off (information can age) is addressed in the
roadmap (Section 4).

---

## 2. Realistic risks and how we mitigate them

### Risk 1 — Hallucinated or wrong benefit information (highest-stakes risk)

If Tara invents a subsidy, a requirement, or a deadline, a person in poverty could waste
a bus fare they don't have, miss a real benefit, or be humiliated at an office. This is
the risk we take most seriously.

**Mitigations built into the system prompt:**
- An absolute rule: *"Never invent information. If you are not certain, say so and point
  to where to verify it."*
- Every program Tara names **must** cite its responsible entity and official channel
  (website or toll-free number), so the user can always confirm at the source.
- Tara is constrained to a **closed, curated knowledge base** rather than open-ended
  generation about benefits.
- When asked something outside its knowledge, Tara is required to say so and redirect to
  the relevant official entity instead of guessing.

### Risk 2 — Privacy of sensitive personal data

To orient a user, Tara may learn income, household composition, disability, displacement
/ victim status, and migration status — sensitive data, sometimes about minors.

**Mitigations:**
- **Data minimization by design:** one or two questions per turn, never a full form;
  Tara is instructed to *never pressure* and to work with whatever the user is willing
  to share.
- **No long-term persistence:** conversation state lives only in ephemeral, in-process
  memory. We do **not** write user data to a database and we do **not** sell, share, or
  use it for any purpose beyond answering the current conversation.
- **No unnecessary identifiers:** Tara does not need or request full national ID numbers;
  sessions are keyed by an opaque WhatsApp identifier, not by name.
- **Disclosed processors only:** the only third parties that see message content are the
  ones disclosed above (Meta/WhatsApp as the channel, Groq as the model provider).

*Committed improvements (see roadmap):* automatic session expiry/retention limits and a
clear in-chat privacy notice on first contact.

### Risk 3 — Over-reliance / replacing human institutions

A chatbot must not become the thing that decides whether a poor family eats.

**Mitigations — an explicit "Limits of the Agent" section in the prompt:**
- Tara **never decides eligibility or SISBEN category** — only a state official can,
  after an official visit/verification.
- Tara is forbidden from saying *"you qualify"* as fact; it must say *"you could
  qualify"* / *"I recommend you verify"* and always name the office to confirm with.
- Legal, medical, and violence-related issues are explicitly handed off to professionals
  and institutions, never resolved by the bot.

### Risk 4 — Harm in crisis situations

**Mitigation:** Tara is instructed to detect urgency (no food, no shelter, danger) and
domestic-violence disclosures, prioritize them, and surface emergency human resources
(Línea 155 for gender violence, ICBF Línea 141, Línea Social 106) before anything else.

### Risk 5 — Unfair exclusion / bias

A naive system might exclude someone because they *reported* a wrong SISBEN category.

**Mitigation:** a **coherence rule** instructs Tara to flag, with tact, when a declared
category contradicts the rest of the profile, and to **never deny a benefit based solely
on a self-declared category** — protecting users from being wrongly screened out.

---

## 3. Where human judgment remains central

Tara is an **orientation layer, not a decision layer**. Human judgment is preserved at
three levels:

1. **The citizen decides.** Tara informs and explains *why* each option fits the user's
   case; the person chooses what to pursue. We empower the human decision, we don't
   replace it.
2. **The state official decides.** Final eligibility and SISBEN classification are made
   by an authorized human after official verification. Tara's output is always
   subordinate to that human check.
3. **Professionals own specialized domains.** Legal, medical, and safety matters are
   routed to humans (free university legal clinics, EPS, Defensoría, emergency lines).

This is human-in-the-loop by design: the AI lowers the cost of *understanding* rights,
while every consequential decision stays with a qualified person.

---

## 4. Responsible roadmap

- Add a **retrieval layer (RAG) over official government sources** so facts stay current
  and every answer is traceable to a live document.
- Add **automatic session retention limits** and a first-contact privacy notice.
- Add a lightweight **answer-confidence / "verify here" footer** on benefit claims.
- Periodic human review of the curated knowledge base against official sources.
