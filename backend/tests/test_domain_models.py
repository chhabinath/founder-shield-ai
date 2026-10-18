from app.schemas.domain import (
    BriefContent, BriefVersion, InterviewRecord, InterviewSession,
    SessionStatus, AnswerSource,
)


def test_session_defaults():
    s = InterviewSession(owner_id="o1")
    assert s.status == SessionStatus.CREATED
    assert s.question_count == 0
    assert s.id


def test_version_hash_is_frozen_from_content():
    c = BriefContent(title="A", problem_statement="P")
    v = BriefVersion(brief_id="b1", owner_id="o1", version_number=1, content=c)
    assert v.content_hash == c.content_hash()
    assert len(v.content_hash) == 64  # sha256 hex


def test_hash_changes_with_content():
    v1 = BriefVersion(brief_id="b", owner_id="o", version_number=1,
                      content=BriefContent(title="A"))
    v2 = BriefVersion(brief_id="b", owner_id="o", version_number=2,
                      content=BriefContent(title="B"))
    assert v1.content_hash != v2.content_hash


def test_record_has_no_audio_field():
    r = InterviewRecord(session_id="s", owner_id="o",
                        question_key="problem", question_text="?",
                        answer_text="[redacted]")
    assert r.source == AnswerSource.FOUNDER
    assert not hasattr(r, "audio")
    assert not hasattr(r, "raw_transcript")
