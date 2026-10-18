# FounderShield AI — Implementation Plan

> **Status:** Phase 00 planning document. Phases execute one at a time; each
> ends with a report and an explicit stop.

## Phase ledger

| Phase | Title | Primary outputs | Depends on | Status |
|-------|-------|-----------------|-----------|--------|
| 00 | Repo audit & plan | docs + `.env.example` | — | **DONE (this phase)** |
| 01 | Application foundation | FastAPI skeleton, health, logging, CORS, Vite/React/TS shell, typed client | 00 | pending |
| 02 | DB, auth, session isolation | Models, migrations, RLS, repo interfaces + test doubles | 01 | **DONE** |
| 03 | Privacy guard & policy gateway | Detection, redaction, policy decision, adversarial tests | 01 | **DONE** |
| 04 | Stateful interview engine | State machine, adaptive follow-ups, mock interview | 02, 03 | **DONE** |
| 05 | Voice-provider adapter | Interface + mock; verified docs; selected **Smallest AI** | 04 | **DONE** |
| 06 | Structured brief generation | Pydantic brief schema, LLM interface + mock, validation/retry | 03, 04 | pending |
| 07 | Review, versioning, approval | Review UI, immutable versions, approval/export enforcement | 06 | pending |
| 08 | Integration & security testing | E2E (mock providers), security test suite | 01–07 | pending |
| 09 | Demo readiness & deployment | Setup docs, env validation, deployment checklist, demo | 08 | pending |

## Working protocol (every phase)

A. Inspect relevant files and current implementation.
B. Summarize intended changes and uncertainties.
C. Implement only the requested phase.
D. Run tests / lint / type checks / builds.
E. Report: files changed, decisions, commands, test results, limitations,
   security considerations, exact next step.

Rules: inspect before changing; preserve working code; never invent SDK methods,
endpoints, env vars, schemas, or provider capabilities; mock providers when
credentials are unavailable; no paid resources or deployments without explicit
permission; small reviewable changes with tests after each step.

## Missing architecture decisions (to resolve, by phase)

- **AD-1 (Phase 05): RESOLVED** - backend mints a short-lived single-use token (Smallest AI register-call); the browser opens the WebSocket directly via the official SDK. API key stays server-side.
- **AD-2 (Phase 06):** LLM provider + configuration schema.
- **AD-3 (Phase 09):** deployment target, production CORS origins.
- **AD-4 (Phase 02/03):** transcript handling — redact-then-retain vs discard.
- **AD-5 (Phase 02): RESOLVED** — cross-owner access returns **404 `not_found`** (not 403) to avoid resource enumeration, consistent with RLS making other owners' rows invisible.

## Unresolved provider questions (verify in Phase 05 against official docs)

> These are **open questions**, not assumptions. None of the capabilities below
> are presented as facts. Each must be confirmed against current official
> documentation before any real integration.

- UPQ-1: Does each provider (Bolna, Smallest AI, Sarvam) support direct -> RESOLVED (Smallest=browser SDK; Bolna=telephony; Sarvam=frameworks)
  **browser** voice sessions, or only server-side/telephony? Unverified.
- UPQ-2: What is each provider's authentication model (API key, token, OAuth)? -> RESOLVED (Smallest/Bolna Bearer; Sarvam X-API-Key; Smallest adds browser token)
  Unverified.
- UPQ-3: How are **transcripts** delivered (streaming events, webhooks, poll)? -> RESOLVED (Smallest=WS events; Bolna=poll/webhook; Sarvam=framework)
  Unverified.
- UPQ-4: Interruption/barge-in support per provider? Unverified. -> RESOLVED (client-side SDK/framework concern)
- UPQ-5: Pricing / free credits available for the demo? Unverified. -> RESOLVED (not integrated; no credits spent; mock used)
- UPQ-6: Data-handling / retention terms of each provider (needed for the -> STILL OPEN (provider data-handling/retention terms before real content)
  Phase 05 data-flow review before sending any interview content)? Unverified.

## Immediate next step

Await explicit instruction to begin **Phase 06 — Structured problem-brief generation**.
Phases do not auto-advance.
