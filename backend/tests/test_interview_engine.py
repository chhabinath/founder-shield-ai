"""Phase 04 interview-engine tests (no voice provider)."""
import pytest

from app.schemas.domain import AnswerSource, SessionStatus
from app.repositories.memory import (
    InMemorySessionRepository,
    InMemoryInterviewRecordRepository,
)
from app.services.privacy.gateway import PrivacyGateway
from app.services.interview import questions as Q
from app.services.interview.engine import (
    InterviewEngine, InterviewConfig,
    SessionPaused, SessionNotActive, UnknownQuestionKey, DuplicateAnswer,
)
from app.services.interview.mock import run_mock_interview, DEFAULT_ANSWERS
from app.services.authz import ResourceNotFound


def make_engine(config=None):
    return InterviewEngine(
        InMemorySessionRepository(),
        InMemoryInterviewRecordRepository(),
        PrivacyGateway(),
        config or InterviewConfig(),
    )


def test_full_run_reaches_ready_for_brief():
    eng = make_engine()
    session, records = run_mock_interview(eng, "owner-A")
    assert session.status == SessionStatus.READY_FOR_BRIEF
    # Every required topic has a founder answer.
    founder = [r for r in records if r.source == AnswerSource.FOUNDER]
    covered = {r.question_key for r in founder}
    for topic in Q.REQUIRED_TOPICS:
        assert topic in covered


def test_one_question_at_a_time_and_order():
    eng = make_engine()
    s = eng.start("owner-A")
    first = eng.next_question(s.id, "owner-A")
    assert first.has_question
    assert first.question.topic == "problem"  # first required topic
    assert first.question.kind.value == "core"


def test_first_submit_moves_to_in_progress():
    eng = make_engine()
    s = eng.start("owner-A")
    assert s.status == SessionStatus.CREATED
    r = eng.submit_answer(s.id, "owner-A", "problem",
                          "Tickets pile up overnight and nobody triages them.")
    assert r.accepted
    assert r.status == SessionStatus.IN_PROGRESS.value


def test_thin_answer_triggers_followup():
    eng = make_engine()
    s = eng.start("owner-A")
    eng.submit_answer(s.id, "owner-A", "problem", "too slow")  # thin (<15 chars)
    nxt = eng.next_question(s.id, "owner-A")
    assert nxt.has_question
    assert nxt.question.kind.value == "follow_up"
    assert nxt.question.topic == "problem"


def test_substantive_answer_skips_followup():
    eng = make_engine()
    s = eng.start("owner-A")
    eng.submit_answer(s.id, "owner-A", "problem",
                      "Tickets pile up overnight and nobody triages them until noon.")
    nxt = eng.next_question(s.id, "owner-A")
    assert nxt.question.topic == "affected_users"  # moved on, no follow-up


def test_followup_capped_per_topic():
    eng = make_engine(InterviewConfig(max_follow_ups_per_topic=1))
    s = eng.start("owner-A")
    eng.submit_answer(s.id, "owner-A", "problem", "slow")       # thin core
    fu = eng.next_question(s.id, "owner-A")
    assert fu.question.key == "problem.followup"
    eng.submit_answer(s.id, "owner-A", "problem.followup", "bad")  # thin follow-up too
    nxt = eng.next_question(s.id, "owner-A")
    # No second follow-up for the same topic; move on.
    assert nxt.question.topic == "affected_users"


def test_dont_know_is_accepted_and_moves_on():
    eng = make_engine()
    s = eng.start("owner-A")
    r = eng.submit_answer(s.id, "owner-A", "problem", is_dont_know=True)
    assert r.accepted
    nxt = eng.next_question(s.id, "owner-A")
    assert nxt.question.topic == "affected_users"  # no follow-up on don't-know


def test_privacy_block_during_interview_not_stored():
    eng = make_engine()
    s = eng.start("owner-A")
    # A long unclassifiable high-entropy token -> gateway fails closed.
    token = "Zx9Q" + "7fKp2Lm8Rt4Vn6Wb3Yc5Hd1Ja0" + "Qq2"
    r = eng.submit_answer(s.id, "owner-A", "problem", f"the id is {token}")
    assert not r.accepted
    assert r.blocked_for_privacy
    assert r.requires_user_correction
    # nothing stored
    assert eng.records.list_for_session(s.id, "owner-A") == []


def test_email_in_answer_is_redacted_before_storage():
    eng = make_engine()
    s = eng.start("owner-A")
    eng.submit_answer(s.id, "owner-A", "problem",
                      "Escalations go to founder@startup-example.com every night.")
    rec = eng.records.list_for_session(s.id, "owner-A")[0]
    assert "founder@startup-example.com" not in rec.answer_text
    assert "[EMAIL_REDACTED]" in rec.answer_text


def test_duplicate_answer_rejected():
    eng = make_engine()
    s = eng.start("owner-A")
    eng.submit_answer(s.id, "owner-A", "problem", "a sufficiently long answer here")
    with pytest.raises(DuplicateAnswer):
        eng.submit_answer(s.id, "owner-A", "problem", "another answer")


def test_unknown_question_key_rejected():
    eng = make_engine()
    s = eng.start("owner-A")
    with pytest.raises(UnknownQuestionKey):
        eng.submit_answer(s.id, "owner-A", "not_a_topic", "whatever")


def test_pause_blocks_then_resume_allows():
    eng = make_engine()
    s = eng.start("owner-A")
    eng.submit_answer(s.id, "owner-A", "problem", "a sufficiently long answer here")
    eng.pause(s.id, "owner-A")
    with pytest.raises(SessionPaused):
        eng.next_question(s.id, "owner-A")
    with pytest.raises(SessionPaused):
        eng.submit_answer(s.id, "owner-A", "affected_users", "some people")
    eng.resume(s.id, "owner-A")
    nxt = eng.next_question(s.id, "owner-A")
    assert nxt.has_question


def test_cancel_is_terminal():
    eng = make_engine()
    s = eng.start("owner-A")
    eng.cancel(s.id, "owner-A")
    reloaded = eng.get_session(s.id, "owner-A")
    assert reloaded.status == SessionStatus.CANCELLED
    with pytest.raises(SessionNotActive):
        eng.submit_answer(s.id, "owner-A", "problem", "too late now friend")


def test_session_isolation_between_owners():
    eng = make_engine()
    s = eng.start("owner-A")
    # owner-B cannot see or act on owner-A's session.
    with pytest.raises(ResourceNotFound):
        eng.get_session(s.id, "owner-B")
    with pytest.raises(ResourceNotFound):
        eng.submit_answer(s.id, "owner-B", "problem", "cross owner attempt here")


def test_ai_suggestion_does_not_satisfy_coverage():
    eng = make_engine()
    s = eng.start("owner-A")
    # An AI suggestion for "problem" must NOT count as the founder answer.
    eng.record_ai_suggestion(s.id, "owner-A", "problem", "Maybe it is triage latency.")
    nxt = eng.next_question(s.id, "owner-A")
    assert nxt.question.topic == "problem"  # still asking problem
    assert nxt.question.kind.value == "core"


def test_max_questions_cap_forces_ready():
    eng = make_engine(InterviewConfig(max_questions=3))
    s = eng.start("owner-A")
    for key in ["problem", "affected_users", "current_process"]:
        eng.submit_answer(s.id, "owner-A", key,
                          "A clear and sufficiently detailed answer about it.")
    nxt = eng.next_question(s.id, "owner-A")
    assert not nxt.has_question
    assert nxt.status == SessionStatus.READY_FOR_BRIEF.value


def test_next_question_is_idempotent():
    eng = make_engine()
    s = eng.start("owner-A")
    a = eng.next_question(s.id, "owner-A")
    b = eng.next_question(s.id, "owner-A")
    assert a.question.key == b.question.key  # no repeat/advance without an answer
