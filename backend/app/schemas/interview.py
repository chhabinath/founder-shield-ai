"""Interview engine data contracts (Pydantic v2).

NOTE: no `from __future__ import annotations` here so Pydantic resolves the
annotations eagerly (consistent with app/schemas/domain.py).
"""
import enum

from pydantic import BaseModel, Field


class QuestionKind(str, enum.Enum):
    CORE = "core"
    FOLLOW_UP = "follow_up"


class Question(BaseModel):
    key: str
    topic: str
    kind: QuestionKind
    text: str


class NextQuestionResult(BaseModel):
    has_question: bool
    question: Question | None = None
    status: str
    answered_count: int = 0
    remaining_required: list[str] = Field(default_factory=list)


class SubmitResult(BaseModel):
    accepted: bool
    status: str
    blocked_for_privacy: bool = False
    requires_user_correction: bool = False
    reasons: list[str] = Field(default_factory=list)
    answered_count: int = 0
