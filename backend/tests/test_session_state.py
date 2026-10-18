import pytest

from app.schemas.domain import SessionStatus as S
from app.services.session_state import (
    can_transition, ensure_transition, InvalidStateTransition,
)


@pytest.mark.parametrize("src,dst", [
    (S.CREATED, S.IN_PROGRESS),
    (S.IN_PROGRESS, S.READY_FOR_BRIEF),
    (S.READY_FOR_BRIEF, S.REVIEW_REQUIRED),
    (S.REVIEW_REQUIRED, S.APPROVED),
    (S.APPROVED, S.EXPORTED),
    (S.APPROVED, S.REVIEW_REQUIRED),
    (S.EXPORTED, S.REVIEW_REQUIRED),
])
def test_valid_transitions(src, dst):
    assert can_transition(src, dst)
    ensure_transition(src, dst)  # no raise


@pytest.mark.parametrize("src,dst", [
    (S.CREATED, S.APPROVED),
    (S.CREATED, S.EXPORTED),
    (S.IN_PROGRESS, S.EXPORTED),
    (S.CANCELLED, S.IN_PROGRESS),
    (S.EXPORTED, S.APPROVED),
    (S.REVIEW_REQUIRED, S.EXPORTED),
])
def test_invalid_transitions_rejected(src, dst):
    assert not can_transition(src, dst)
    with pytest.raises(InvalidStateTransition):
        ensure_transition(src, dst)
