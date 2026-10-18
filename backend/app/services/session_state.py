"""Session lifecycle transitions (authoritative, server-side).

This is the Phase 02 foundation for invalid-transition rejection. The full
interview engine (Phase 04) builds its behaviour on top of this map; the
allowed edges here mirror the state diagram in docs/API_CONTRACTS.md.
"""
from __future__ import annotations

from app.schemas.domain import SessionStatus

S = SessionStatus

# Directed adjacency: state -> allowed next states.
ALLOWED_TRANSITIONS: dict[SessionStatus, set[SessionStatus]] = {
    S.CREATED: {S.IN_PROGRESS, S.CANCELLED},
    S.IN_PROGRESS: {S.IN_PROGRESS, S.READY_FOR_BRIEF, S.CANCELLED},
    S.READY_FOR_BRIEF: {S.REVIEW_REQUIRED, S.CANCELLED},
    S.REVIEW_REQUIRED: {S.REVIEW_REQUIRED, S.APPROVED, S.CANCELLED},
    S.APPROVED: {S.REVIEW_REQUIRED, S.EXPORTED},
    S.EXPORTED: {S.REVIEW_REQUIRED},
    S.CANCELLED: set(),
}


class InvalidStateTransition(Exception):
    def __init__(self, src: SessionStatus, dst: SessionStatus) -> None:
        super().__init__(f"invalid transition {src.value} -> {dst.value}")
        self.src = src
        self.dst = dst


def can_transition(src: SessionStatus, dst: SessionStatus) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, set())


def ensure_transition(src: SessionStatus, dst: SessionStatus) -> None:
    if not can_transition(src, dst):
        raise InvalidStateTransition(src, dst)
