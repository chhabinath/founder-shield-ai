# FounderShield AI - Voice Integration (Phase 05)

> Status: provider-independent interface + mock implemented and tested.
> One real provider (Smallest AI) implemented at the documented
> token-minting step only, and UNVERIFIED against the live service (no
> credentials available). Mock remains the default.

## Provider comparison (verified against official docs on 2026-10-18)

| Capability | Smallest AI | Bolna | Sarvam |
|------------|-------------|-------|--------|
| Browser voice session | First-class: browser WebSocket SDK `@smallest-ai/agent-sdk` + browser cookbook | Telephony-first (inbound/outbound phone); browser mentioned but quickstart is phone + wallet credits | Via third-party orchestration (Vapi / LiveKit / Pipecat) |
| Auth model | Bearer API key server-side; mints a short-lived (~30s) single-use token for the browser | Bearer API key | `X-API-Key` header |
| Transcript delivery | Realtime WebSocket message types | Poll execution or webhook after a call | Through the orchestration framework |
| Server step we implement | `POST /atoms/v1/conversation/register-call` to mint the token | create agent + place call (phone) | n/a (framework-driven) |
| Cost shape | Web session, no telephony leg required | Wallet credits per phone call | Telephony-oriented |

Sources: Smallest AI API intro + register-call + browser SDK/cookbook;
Bolna API quickstart + voice-agents overview; Sarvam voice-agents intro +
LiveKit/Pipecat/Vapi integration guides.

## Decision: Smallest AI

Chosen because it is the only provider with a **documented first-class
browser path**, and its **register-call token flow keeps our API key
server-side** while handing the browser only a short-lived single-use token.
That matches our security model directly ("no secrets in browser code",
backend-mediated authorization). Bolna is telephony-first (needs a phone
number and spends wallet credits per call - a credit-burn risk and a poor
fit for an in-app founder interview). Sarvam needs an extra orchestration
framework to run the browser voice loop.

## What is implemented (and what is NOT)

- IMPLEMENTED (server-side): `SmallestVoiceProvider.start_session()` performs
  the documented `register-call` POST and returns the short-lived client
  token in a normalized `VoiceSessionResult`. Request/response SHAPE is
  verified against the docs and covered by tests using `httpx.MockTransport`
  (no network, no credentials).
- NOT implemented (by design): the browser-side WebSocket audio loop. Per the
  docs that is owned by the official `@smallest-ai/agent-sdk` running in the
  browser with the short-lived token. We do NOT invent WebSocket server code
  or SDK method names.

## Data-flow review (required before sending interview content)

- The backend only mints a session token; it does not send interview answers
  to the provider in this phase.
- When live audio is wired up later, transcripts returning from the provider
  MUST pass through the Phase 03 privacy gateway before storage, exactly like
  typed answers do today. No raw transcript is persisted by default.
- The provider's own data-handling / retention terms must be confirmed before
  any real interview content flows (open item UPQ-6).

## Configuration

- `VOICE_PROVIDER` = `mock` (default) | `smallest`
- `VOICE_API_KEY`  = server-side key (never shipped to the browser)
- `VOICE_AGENT_ID` = the Atoms agent id to connect to
- In production, a non-mock `VOICE_PROVIDER` requires both `VOICE_API_KEY`
  and `VOICE_AGENT_ID` (enforced at config load). Missing creds in dev fall
  back to the mock provider rather than failing.

## Resolved open questions (were UPQ-1..6)

- UPQ-1 browser support: Smallest = yes (SDK); Bolna = telephony-first; Sarvam = via frameworks.
- UPQ-2 auth: Smallest/Bolna = Bearer key; Sarvam = X-API-Key. Smallest adds a browser token flow.
- UPQ-3 transcript: Smallest = WS events; Bolna = poll/webhook; Sarvam = framework.
- UPQ-4 interruption/barge-in: handled client-side by the provider SDK / framework; not a backend concern in this phase.
- UPQ-5 pricing: not integrated; no credits spent. Mock used throughout.
- UPQ-6 data handling/retention terms: STILL OPEN - must be confirmed before real interview content is sent.
