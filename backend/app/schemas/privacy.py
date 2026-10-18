"""Privacy guard data contracts.

IMPORTANT: A Finding never stores the raw sensitive substring. It carries
only the category, a confidence score, whether it is safely redactable, and
the character span (offsets) needed to perform redaction. Audit/log output
is built from category + confidence + redactable only -- never raw values.
"""
import enum

from pydantic import BaseModel, Field


class SensitiveCategory(str, enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    API_KEY = "api_key"
    AWS_ACCESS_KEY = "aws_access_key"
    BEARER_TOKEN = "bearer_token"
    CREDENTIAL_ASSIGNMENT = "credential_assignment"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    PRIVATE_KEY = "private_key"
    UNKNOWN_SECRET = "unknown_secret"  # high-entropy, cannot classify -> fail closed


class Finding(BaseModel):
    category: SensitiveCategory
    start: int
    end: int
    confidence: float = Field(ge=0.0, le=1.0)
    redactable: bool
    placeholder: str = "[REDACTED]"

    def summary(self) -> dict:
        """Audit-safe projection: NO raw value, NO offsets."""
        return {
            "category": self.category.value,
            "confidence": round(self.confidence, 3),
            "redactable": self.redactable,
            "length": self.end - self.start,
        }


class PrivacyDecisionType(str, enum.Enum):
    ALLOW = "allow"
    BLOCK = "block"


class PrivacyResult(BaseModel):
    decision: PrivacyDecisionType
    # redacted_text is populated ONLY on ALLOW. None on BLOCK (fail closed).
    redacted_text: str | None = None
    requires_user_correction: bool = False
    reasons: list[str] = Field(default_factory=list)
    findings: list[dict] = Field(default_factory=list)  # audit-safe summaries

    @property
    def allowed(self) -> bool:
        return self.decision == PrivacyDecisionType.ALLOW
