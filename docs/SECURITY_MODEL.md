# FounderShield AI — Security Model

> **Status:** Phase 00 planning document. Describes the intended security
> boundaries that later phases must implement and test.

## 1. Principles

1. **The LLM is never a security boundary.** All authentication, authorization,
   session isolation, redaction, retention, validation, and approval are
   enforced in backend code.
2. **Fail closed.** When a privacy or approval decision is uncertain or unsafe,
   reject the operation.
3. **Least data.** Store only the minimum interview information required. No raw
   audio and no complete raw transcripts by default.
4. **Defense in depth.** Application-level ownership checks AND database
   row-level security.

## 2. Trust boundaries

| Boundary | Untrusted side | Enforcement |
|----------|----------------|-------------|
| Browser → Backend | Browser | JWT verification, owner derivation, authz |
| Backend → Supabase | — | RLS policies scoped to `owner_id` |
| Backend → LLM | LLM (external) | Redaction + policy gateway, redacted payloads only |
| Backend → Voice provider | Provider (external) | Adapter, mock by default, data-flow review before real use |

## 3. AuthN / AuthZ

- Authentication via Supabase Auth (JWT). The backend verifies signature and
  claims on every protected request.
- `owner_id` is derived from the verified token, never from the request body.
- Every session- or brief-scoped request validates that the resource's
  `owner_id` equals the caller. Cross-owner access returns `not_found`
  (decided in Phase 02, AD-5: avoids resource enumeration and matches RLS,
  which makes other owners' rows invisible).
- One session must never retrieve another session's data.

## 4. Privacy guard (Phase 03 contract summary)

Pipeline: `incoming data → schema validation → sensitive-data detection →
redaction → policy decision → authorized downstream processing`.

- Detects at least: email addresses, phone numbers, credential-like strings,
  and API-key patterns. Detection is treated as **imperfect**.
- Redaction happens before any external reasoning-model call.
- If a detected secret cannot be safely redacted, the pipeline **pauses and
  requests founder correction** (fail closed) rather than forwarding.
- Raw sensitive input is never logged. Logs carry redacted content only.
- Redaction/authorization decisions live in backend code and cannot be disabled
  by model output.

## 5. Approval & export integrity (Phase 07 contract summary)

- Each edit creates a new **immutable** `BriefVersion` with a `content_hash`.
- Approval (`ApprovalRecord`) binds to exactly one `brief_version_id` and stores
  the `approved_content_hash`.
- On any content change, existing approvals are invalidated
  (`status = invalidated`); re-approval is required.
- Export requires an `active` approval whose `approved_content_hash` matches the
  version being exported; otherwise `approval_required` / `approval_invalidated`.
- Export is idempotent (`Idempotency-Key`) to prevent duplicate/replayed sends.
- An LLM can never approve or export on behalf of the founder.

## 6. Invalid state transitions

- The interview/brief state machine (see `API_CONTRACTS.md`) rejects any
  undrawn transition with `invalid_state_transition`.
- State is authoritative in the backend/database, not in the client.

## 7. Secrets handling

- Secrets live only in environment variables (or an approved secret manager).
- Secrets are never printed in chat, logs, test output, or source.
- `.env.example` contains **placeholders only**.
- The production build must contain no secrets (verified in Phase 09).

## 8. Retention & deletion (Phase 02 detail)

- Default: redacted interview records retained for a bounded window
  (proposed 30 days — see OPQ-4); founder may delete at any time.
- No raw audio stored. No complete raw transcript stored by default.
- Deletion removes owner-scoped rows and dependent versions/approvals.

## 9. Logging & observability

- Structured logs with a redaction filter applied before emission.
- Error responses never leak secrets, raw sensitive input, or stack traces.

## 10. Residual risks (tracked, revisited in Phase 08)

- Detection is heuristic; novel secret formats may evade redaction → mitigated
  by fail-closed on low-confidence and founder correction step.
- Prompt-injection against the reasoning model → mitigated by treating LLM
  output as untrusted data, Pydantic validation, and no authz via prompt.
- Provider-side data handling → mitigated by redaction + data-flow review.
