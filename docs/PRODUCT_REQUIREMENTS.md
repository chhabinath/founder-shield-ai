# FounderShield AI — Product Requirements

> **Status:** Phase 00 planning document. Describes intended product behavior.
> No application code exists yet (see Repository Audit below).

## 1. Objective

A privacy-first voice interviewer for startup founders that converts vague
operational problems into structured, evidence-backed, build-ready problem
briefs.

## 2. Repository audit (actual starting point)

Audited on 2026-10-18. Repo root:
`C:\Users\chhab\OneDrive\Documents\Projects\hackathon\voiceAgent`

| Area | Finding |
|------|---------|
| Frontend | **None.** No `package.json`, no Vite/React/TS. |
| Backend | **None.** No Python package, no FastAPI app, no `pyproject.toml`/`requirements.txt`. |
| Database / Auth | **None.** No Supabase config, no migrations. |
| AI / reasoning | **None.** |
| Voice | **None.** |
| Tests | **None.** |
| Docs | **None** prior to this phase. |
| Env examples | **None** prior to this phase. |

**Conclusion:** greenfield directory. There is no working code to preserve, so
the folder structure proposed in `ARCHITECTURE.md` can be adopted cleanly.

## 3. Core user journey

1. Founder signs in (Supabase auth).
2. Founder starts an interview session.
3. The system conducts a conversational, one-question-at-a-time interview.
4. The system asks adaptive follow-up questions to clarify missing information.
5. Sensitive data is detected and redacted **in the backend** before any
   external reasoning-model call.
6. The system separates confirmed facts, founder-provided claims, assumptions,
   and unknowns.
7. The system generates a structured problem brief.
8. The founder reviews and edits the brief.
9. The founder gives **explicit, backend-verified approval** of a specific,
   immutable brief version.
10. Only an approved version may be exported or shared.

## 4. Functional requirements

- **FR-1** Conduct a conversational interview covering: problem, affected users,
  current process, impact, evidence, constraints, desired outcome.
- **FR-2** Ask one clear question at a time.
- **FR-3** Ask adaptive follow-up questions when information is missing.
- **FR-4** Support explicit "I don't know" answers.
- **FR-5** Distinguish founder-provided information from AI-generated suggestions.
- **FR-6** Limit interview length and avoid repeated questions.
- **FR-7** Allow pause, resume, and cancel.
- **FR-8** Generate a structured brief validated by Pydantic.
- **FR-9** Classify every brief statement as confirmed fact, founder claim,
  assumption, or unknown.
- **FR-10** Allow the founder to edit every brief field.
- **FR-11** Version briefs; each edit produces a new immutable version.
- **FR-12** Require deliberate approval bound to one immutable version.
- **FR-13** Invalidate approval when approved content changes.
- **FR-14** Permit export/share only with a valid approval; prevent replay.
- **FR-15** Voice interaction through a provider adapter (mock by default).

## 5. Non-functional requirements

- **NFR-1 Privacy:** no unredacted secrets leave the backend to any external
  reasoning model. No raw audio or complete raw transcripts stored by default.
- **NFR-2 Security:** auth, authorization, session isolation, retention,
  validation, and approval are enforced in backend code, never by an LLM prompt.
- **NFR-3 Fail closed:** uncertain or unsafe privacy/approval cases are rejected.
- **NFR-4 Testability:** full workflow runnable with mock voice and mock LLM
  providers, no real credentials required for development.
- **NFR-5 Portability:** provider-specific code lives behind interfaces.
- **NFR-6 Observability:** structured logs with secret/sensitive-data redaction.

## 6. Explicitly out of scope (for now)

- Multi-tenant org/team sharing beyond single-owner isolation.
- Billing / paid resource provisioning.
- Production deployment (decided later; see IMPLEMENTATION_PLAN).
- Real provider integration until credentials and a data-flow review exist.

## 7. Open product questions

- OPQ-1: Target interview length ceiling (max questions)? Proposed default: 15.
- OPQ-2: Which locales/languages must voice support at demo time?
- OPQ-3: Export destinations required for the demo (file download vs. email vs.
  third-party)? Affects Phase 07 approval→export binding.
- OPQ-4: Default retention window for redacted interview records? Proposed: 30
  days, founder-initiated delete at any time.
