"""Stateful interview engine (voice-provider independent).

Responsibilities:
  * Ask one question at a time, in a deterministic order.
  * Ask an adaptive follow-up when a core answer is thin (capped per topic).
  * Support explicit "I don't know" answers.
  * Redact every founder answer via the privacy gateway BEFORE storing;
    a blocked answer is NOT stored and the founder is asked to correct it.
  * Keep founder answers distinct from AI suggestions; only founder answers
    (or explicit "don't know") satisfy required-topic coverage.
  * Enforce session+owner isolation on every operation.
  * Drive ONLY the interview lifecycle (up to READY_FOR_BRIEF). It has no
    path to approval/authorization/export.

`next_question` is a PURE function of the answers recorded so far, so it is
idempotent and never repeats a question that already has an answer.
"""
import logging

from app.schemas.domain import (
    AnswerSource,
    InterviewRecord,
    InterviewSession,
    SessionStatus,
)
from app.schemas.interview import (
    NextQuestionResult,
    Question,
    QuestionKind,
    SubmitResult,
)
from app.services.authz import require_owner
from app.services.interview import questions as Q
from app.services.privacy.gateway import PrivacyGateway
from app.services.session_state import ensure_transition

_logger = logging.getLogger("foundershield.interview")

_ACTIVE = {SessionStatus.CREATED, SessionStatus.IN_PROGRESS}


class InterviewError(Exception):
    """Base class for interview engine errors."""


class SessionPaused(InterviewError):
    pass


class SessionNotActive(InterviewError):
    pass


class UnknownQuestionKey(InterviewError):
    pass


class DuplicateAnswer(InterviewError):
    pass


class InterviewConfig:
    def __init__(
        self,
        max_questions: int = 15,
        max_follow_ups_per_topic: int = 1,
        min_substantive_chars: int = 15,
    ) -> None:
        self.max_questions = max_questions
        self.max_follow_ups_per_topic = max_follow_ups_per_topic
        self.min_substantive_chars = min_substantive_chars


class InterviewEngine:
    def __init__(self, sessions, records, privacy_gateway=None, config=None) -> None:
        self.sessions = sessions
        self.records = records
        self.privacy = privacy_gateway or PrivacyGateway()
        self.config = config or InterviewConfig()

    # ---- lifecycle ---------------------------------------------------
    def start(self, owner_id: str, locale: str = "en", provider: str = "mock") -> InterviewSession:
        session = InterviewSession(owner_id=owner_id, locale=locale, provider=provider)
        return self.sessions.create(session)

    def get_session(self, session_id: str, owner_id: str) -> InterviewSession:
        return require_owner(self.sessions.get(session_id, owner_id), owner_id)

    def pause(self, session_id: str, owner_id: str) -> InterviewSession:
        s = self.get_session(session_id, owner_id)
        if s.status not in _ACTIVE:
            raise SessionNotActive(s.status.value)
        s.paused = True
        return self.sessions.update(s)

    def resume(self, session_id: str, owner_id: str) -> InterviewSession:
        s = self.get_session(session_id, owner_id)
        if s.status not in _ACTIVE:
            raise SessionNotActive(s.status.value)
        s.paused = False
        return self.sessions.update(s)

    def cancel(self, session_id: str, owner_id: str) -> InterviewSession:
        s = self.get_session(session_id, owner_id)
        ensure_transition(s.status, SessionStatus.CANCELLED)
        s.status = SessionStatus.CANCELLED
        s.paused = False
        return self.sessions.update(s)

    # ---- helpers -----------------------------------------------------
    def _founder_records(self, session_id: str, owner_id: str) -> list[InterviewRecord]:
        return [
            r for r in self.records.list_for_session(session_id, owner_id)
            if r.source == AnswerSource.FOUNDER
        ]

    def _record_for_key(self, recs: list[InterviewRecord], key: str):
        return next((r for r in recs if r.question_key == key), None)

    def _covered(self, recs: list[InterviewRecord]) -> set:
        return {t for t in Q.REQUIRED_TOPICS if self._record_for_key(recs, Q.core_key(t))}

    # ---- questioning -------------------------------------------------
    def next_question(self, session_id: str, owner_id: str) -> NextQuestionResult:
        s = self.get_session(session_id, owner_id)
        recs = self._founder_records(session_id, owner_id)
        answered = len(recs)
        remaining = [t for t in Q.REQUIRED_TOPICS if t not in self._covered(recs)]

        if s.paused:
            raise SessionPaused(session_id)
        if s.status not in _ACTIVE:
            # Terminal or already past interviewing: no further questions.
            return NextQuestionResult(
                has_question=False, status=s.status.value,
                answered_count=answered, remaining_required=remaining,
            )

        pending = None
        if answered < self.config.max_questions:
            pending = self._find_pending(recs)

        if pending is not None:
            return NextQuestionResult(
                has_question=True, question=pending, status=s.status.value,
                answered_count=answered, remaining_required=remaining,
            )

        # Nothing pending -> interview complete. Advance IN_PROGRESS -> READY.
        if s.status == SessionStatus.IN_PROGRESS:
            ensure_transition(s.status, SessionStatus.READY_FOR_BRIEF)
            s.status = SessionStatus.READY_FOR_BRIEF
            self.sessions.update(s)
        return NextQuestionResult(
            has_question=False, status=s.status.value,
            answered_count=answered, remaining_required=remaining,
        )

    def _find_pending(self, recs: list[InterviewRecord]):
        for topic in Q.REQUIRED_TOPICS:
            core = self._record_for_key(recs, Q.core_key(topic))
            if core is None:
                return Question(
                    key=Q.core_key(topic), topic=topic,
                    kind=QuestionKind.CORE, text=Q.CORE_QUESTIONS[topic],
                )
            # core answered: decide on a follow-up
            if core.is_dont_know:
                continue
            thin = len(core.answer_text.strip()) < self.config.min_substantive_chars
            if not thin:
                continue
            fu_key = Q.followup_key(topic)
            fu_asked = sum(1 for r in recs if r.question_key == fu_key)
            if fu_asked < self.config.max_follow_ups_per_topic:
                return Question(
                    key=fu_key, topic=topic, kind=QuestionKind.FOLLOW_UP,
                    text=Q.FOLLOW_UP_QUESTIONS[topic],
                )
        return None

    # ---- answering ---------------------------------------------------
    def submit_answer(
        self,
        session_id: str,
        owner_id: str,
        question_key: str,
        answer_text: str = "",
        is_dont_know: bool = False,
    ) -> SubmitResult:
        s = self.get_session(session_id, owner_id)
        if s.status not in _ACTIVE:
            raise SessionNotActive(s.status.value)
        if s.paused:
            raise SessionPaused(session_id)
        if not Q.is_known_key(question_key):
            raise UnknownQuestionKey(question_key)

        recs = self._founder_records(session_id, owner_id)
        if self._record_for_key(recs, question_key) is not None:
            raise DuplicateAnswer(question_key)

        if is_dont_know:
            stored_text = ""
        else:
            result = self.privacy.process(answer_text)
            if not result.allowed:
                # Fail closed: nothing stored, founder asked to correct.
                _logger.info(
                    "interview_answer_blocked session=%s key=%s reasons=%s",
                    session_id, question_key, ",".join(result.reasons),
                )
                return SubmitResult(
                    accepted=False, status=s.status.value,
                    blocked_for_privacy=True,
                    requires_user_correction=result.requires_user_correction,
                    reasons=result.reasons, answered_count=len(recs),
                )
            stored_text = result.redacted_text or ""

        self.records.add(InterviewRecord(
            session_id=session_id, owner_id=owner_id,
            question_key=question_key, question_text="",
            answer_text=stored_text, source=AnswerSource.FOUNDER,
            is_dont_know=is_dont_know,
        ))

        if s.status == SessionStatus.CREATED:
            ensure_transition(SessionStatus.CREATED, SessionStatus.IN_PROGRESS)
            s.status = SessionStatus.IN_PROGRESS

        new_count = len(recs) + 1
        s.question_count = new_count
        self.sessions.update(s)
        return SubmitResult(
            accepted=True, status=s.status.value, answered_count=new_count,
        )

    # ---- AI suggestions (kept DISTINCT from founder answers) ---------
    def record_ai_suggestion(
        self, session_id: str, owner_id: str, question_key: str, suggestion_text: str
    ) -> InterviewRecord:
        """Store an AI suggestion. It never counts toward required coverage."""
        self.get_session(session_id, owner_id)  # ownership check
        return self.records.add(InterviewRecord(
            session_id=session_id, owner_id=owner_id,
            question_key=question_key, question_text="",
            answer_text=suggestion_text, source=AnswerSource.AI_SUGGESTION,
            is_dont_know=False,
        ))
