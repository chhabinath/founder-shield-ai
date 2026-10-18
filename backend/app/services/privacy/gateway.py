"""Privacy policy gateway.

Pipeline:
    incoming data
    -> schema validation
    -> sensitive-data detection
    -> redaction
    -> policy decision
    -> authorized downstream processing

Hard guarantees (enforced in backend code, never by an LLM):
  * Unredactable (unclassifiable) secrets => BLOCK + request user correction.
  * After redaction, a residual re-scan runs; ANY surviving structured
    secret => BLOCK (fail closed). redacted_text is only ever returned on
    ALLOW.
  * Raw input is never logged. Only an audit-safe summary (category,
    confidence, redactable) is emitted.
  * Text embedded in the input cannot alter the decision -- it is data.
"""
import logging

from app.schemas.privacy import (
    PrivacyDecisionType,
    PrivacyResult,
    SensitiveCategory,
)
from app.services.privacy.detectors import detect
from app.services.privacy.redactor import apply_redactions

_logger = logging.getLogger("foundershield.privacy")

# Structured categories that must NEVER survive into a downstream payload.
_RESIDUAL_CRITICAL = {
    SensitiveCategory.EMAIL,
    SensitiveCategory.API_KEY,
    SensitiveCategory.AWS_ACCESS_KEY,
    SensitiveCategory.BEARER_TOKEN,
    SensitiveCategory.CREDIT_CARD,
    SensitiveCategory.SSN,
    SensitiveCategory.PRIVATE_KEY,
    SensitiveCategory.CREDENTIAL_ASSIGNMENT,
}


class PrivacyGateway:
    def __init__(self, max_input_chars: int = 20000) -> None:
        self.max_input_chars = max_input_chars

    def process(self, raw: object) -> PrivacyResult:
        # 1) schema validation (fail closed on malformed input)
        if not isinstance(raw, str):
            return PrivacyResult(
                decision=PrivacyDecisionType.BLOCK,
                reasons=["invalid_input_type"],
            )
        if not raw.strip():
            return PrivacyResult(
                decision=PrivacyDecisionType.BLOCK,
                reasons=["empty_input"],
            )
        if len(raw) > self.max_input_chars:
            return PrivacyResult(
                decision=PrivacyDecisionType.BLOCK,
                reasons=["input_too_large"],
            )

        # 2) detection
        findings = detect(raw)
        summaries = [f.summary() for f in findings]

        # 3) unredactable secret -> fail closed, ask for correction
        if any(not f.redactable for f in findings):
            self._audit("privacy_block_unredactable", summaries)
            return PrivacyResult(
                decision=PrivacyDecisionType.BLOCK,
                requires_user_correction=True,
                reasons=["unredactable_secret_detected"],
                findings=summaries,
            )

        # 4) redaction
        redacted = apply_redactions(raw, findings)

        # 5) residual re-scan (fail closed if anything critical survived)
        residual = [
            f for f in detect(redacted)
            if f.category in _RESIDUAL_CRITICAL
        ]
        if residual:
            self._audit("privacy_block_residual", summaries)
            return PrivacyResult(
                decision=PrivacyDecisionType.BLOCK,
                requires_user_correction=True,
                reasons=["residual_secret_after_redaction"],
                findings=summaries,
            )

        # 6) authorized downstream payload
        self._audit("privacy_allow", summaries)
        return PrivacyResult(
            decision=PrivacyDecisionType.ALLOW,
            redacted_text=redacted,
            findings=summaries,
        )

    def _audit(self, event: str, summaries: list[dict]) -> None:
        # Audit-safe: counts + categories only. Never the raw input.
        categories = sorted({s["category"] for s in summaries})
        _logger.info("%s findings=%d categories=%s",
                     event, len(summaries), ",".join(categories))
