"""Core domain models and enums (Pydantic v2).

Data-minimization notes:
- No raw audio is modelled or stored anywhere.
- `InterviewRecord.answer_text` holds REDACTED text only (see Phase 03).
- Only the minimum fields required by the product are persisted.
"""

import enum
import hashlib
import json
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


class SessionStatus(str, enum.Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_BRIEF = "READY_FOR_BRIEF"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"
    CANCELLED = "CANCELLED"


class AnswerSource(str, enum.Enum):
    FOUNDER = "founder"
    AI_SUGGESTION = "ai_suggestion"


class ApprovalStatus(str, enum.Enum):
    ACTIVE = "active"
    INVALIDATED = "invalidated"


class Owner(BaseModel):
    id: str = Field(default_factory=_new_id)
    email: str
    created_at: datetime = Field(default_factory=_utcnow)


class InterviewSession(BaseModel):
    id: str = Field(default_factory=_new_id)
    owner_id: str
    status: SessionStatus = SessionStatus.CREATED
    locale: str = "en"
    provider: str = "mock"
    question_count: int = 0
    # Pause flag for the interview; does NOT affect lifecycle status
    # (brief/approval). Pause/resume toggle this; cancel clears it.
    paused: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class InterviewRecord(BaseModel):
    id: str = Field(default_factory=_new_id)
    session_id: str
    owner_id: str
    question_key: str
    question_text: str
    # REDACTED answer text only. Never raw transcript / audio.
    answer_text: str
    source: AnswerSource = AnswerSource.FOUNDER
    is_dont_know: bool = False
    created_at: datetime = Field(default_factory=_utcnow)


class BriefContent(BaseModel):
    """Structured brief body. Full generation lands in Phase 06."""
    title: str = ""
    problem_statement: str = ""
    affected_users: str = ""
    current_process: str = ""
    evidence: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    desired_outcome: str = ""
    success_metrics: list[str] = Field(default_factory=list)
    confirmed_facts: list[str] = Field(default_factory=list)
    founder_provided_claims: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)

    def content_hash(self) -> str:
        """Stable SHA-256 over canonical JSON (sorted keys)."""
        canonical = json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ProblemBrief(BaseModel):
    id: str = Field(default_factory=_new_id)
    session_id: str
    owner_id: str
    current_version_id: str | None = None
    status: str = "draft"
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class BriefVersion(BaseModel):
    """Immutable brief version. `content_hash` is computed at creation."""
    id: str = Field(default_factory=_new_id)
    brief_id: str
    owner_id: str
    version_number: int
    content: BriefContent
    content_hash: str = ""
    created_by: str = "founder"  # founder | ai
    created_at: datetime = Field(default_factory=_utcnow)

    def model_post_init(self, _context) -> None:  # noqa: ANN001
        # Freeze the hash from content if not explicitly provided.
        if not self.content_hash:
            self.content_hash = self.content.content_hash()


class ApprovalRecord(BaseModel):
    id: str = Field(default_factory=_new_id)
    brief_version_id: str
    owner_id: str
    approved_content_hash: str
    destination: str | None = None
    status: ApprovalStatus = ApprovalStatus.ACTIVE
    approved_at: datetime = Field(default_factory=_utcnow)
    invalidated_at: datetime | None = None


class AuditEvent(BaseModel):
    """Audit trail WITHOUT sensitive payloads."""
    id: str = Field(default_factory=_new_id)
    owner_id: str
    session_id: str | None = None
    event_type: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)
