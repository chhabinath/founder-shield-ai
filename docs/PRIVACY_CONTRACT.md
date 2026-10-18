# FounderShield AI — Privacy Guard Contract (Phase 03)

The privacy guard is the **authoritative privacy boundary** between
interview data and any external reasoning model. The Phase 01 logging
redaction filter is a secondary safety net, not this boundary.

## Pipeline

```
incoming data
  -> schema validation        (type / non-empty / size bounds)
  -> sensitive-data detection  (structured detectors + high-entropy)
  -> redaction                 (typed placeholders, context preserved)
  -> policy decision           (allow / block, fail closed)
  -> authorized downstream     (redacted_text only, ONLY on allow)
```

## Contract

`PrivacyGateway.process(raw: object) -> PrivacyResult`

- **Input:** any object. Non-string, empty/whitespace, or oversized input is
  rejected (BLOCK) — the gateway validates, it does not trust the caller.
- **Output:** `PrivacyResult`:
  - `decision`: `allow` | `block`
  - `redacted_text`: populated **only** on `allow`; `None` on `block`
    (nothing is ever forwarded on block — fail closed).
  - `requires_user_correction`: `True` when a detected secret cannot be
    safely redacted, or a secret survived redaction (residual).
  - `reasons`: machine-readable codes (`invalid_input_type`, `empty_input`,
    `input_too_large`, `unredactable_secret_detected`,
    `residual_secret_after_redaction`).
  - `findings`: **audit-safe** summaries only — `{category, confidence,
    redactable, length}`. Never the raw substring, never offsets+value.

## Guarantees (enforced in backend code, never by an LLM)

1. Unredacted secrets are never placed in `redacted_text`.
2. Detected-but-unclassifiable secrets (high-entropy unknown tokens) →
   BLOCK + `requires_user_correction` (the "ask the founder to fix it" path).
3. After redaction a **residual re-scan** runs; any surviving structured
   secret → BLOCK (fail closed).
4. Raw sensitive input is never logged. Only category/count audit summaries.
5. Text embedded in the input (e.g. "ignore the privacy policy") is data and
   cannot change the decision.

## Detected categories

email, phone, API keys (`sk-…`), AWS access keys (`AKIA…`), bearer tokens,
credential assignments (`password=…`, value redacted / key kept), credit
cards (Luhn-validated), SSNs, PEM private-key blocks, and a catch-all
high-entropy "unknown secret" that fails closed.

## Known limitations (detection is imperfect — by design)

- Heuristic detectors can miss novel secret formats; the high-entropy
  catch-all + fail-closed residual scan are the backstops.
- The high-entropy detector may flag a legitimate long opaque identifier and
  force a correction prompt. This is the intended conservative trade-off:
  uncertain → fail closed rather than risk a leak.
- Redaction placeholders are typed (`[EMAIL_REDACTED]`, …) so downstream
  reasoning keeps structural context without the sensitive value.

## Configuration

- `max_input_chars` (default 20000) bounds input size.
- Retention/deletion of redacted records is governed by
  `INTERVIEW_RETENTION_DAYS` (Phase 02) and the data-minimization rules in
  `SECURITY_MODEL.md`.
