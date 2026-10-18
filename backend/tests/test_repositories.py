from datetime import datetime, timedelta, timezone

from app.schemas.domain import (
    InterviewSession, InterviewRecord, ProblemBrief, BriefVersion,
    BriefContent, ApprovalRecord, ApprovalStatus,
)
from app.repositories.memory import (
    InMemorySessionRepository, InMemoryInterviewRecordRepository,
    InMemoryBriefVersionRepository, InMemoryApprovalRepository,
)
from app.services.retention import purge_expired


def test_session_isolation_between_owners():
    repo = InMemorySessionRepository()
    a = repo.create(InterviewSession(owner_id="A"))
    b = repo.create(InterviewSession(owner_id="B"))
    # Owner A cannot read B's session.
    assert repo.get(b.id, "A") is None
    assert repo.get(a.id, "A") is a
    # list is scoped.
    assert [s.id for s in repo.list_for_owner("A")] == [a.id]


def test_cross_owner_delete_blocked():
    repo = InMemorySessionRepository()
    s = repo.create(InterviewSession(owner_id="A"))
    assert repo.delete(s.id, "B") is False
    assert repo.get(s.id, "A") is s
    assert repo.delete(s.id, "A") is True
    assert repo.get(s.id, "A") is None


def test_records_scoped_to_session_and_owner():
    repo = InMemoryInterviewRecordRepository()
    repo.add(InterviewRecord(session_id="s1", owner_id="A",
                             question_key="q", question_text="?",
                             answer_text="[r]"))
    repo.add(InterviewRecord(session_id="s1", owner_id="B",
                             question_key="q", question_text="?",
                             answer_text="[r]"))
    got = repo.list_for_session("s1", "A")
    assert len(got) == 1 and got[0].owner_id == "A"


def test_approval_invalidation():
    versions = InMemoryBriefVersionRepository()
    approvals = InMemoryApprovalRepository()
    v = versions.add(BriefVersion(brief_id="b", owner_id="A",
                                  version_number=1, content=BriefContent(title="X")))
    appr = approvals.add(ApprovalRecord(brief_version_id=v.id, owner_id="A",
                                        approved_content_hash=v.content_hash))
    assert approvals.get_active_for_version(v.id, "A") is not None
    n = approvals.invalidate_for_brief("b", "A", [v.id])
    assert n == 1
    assert approvals.get_active_for_version(v.id, "A") is None
    assert appr.status == ApprovalStatus.INVALIDATED


def test_retention_purges_only_expired_for_owner():
    repo = InMemorySessionRepository()
    old = InterviewSession(owner_id="A",
                           created_at=datetime.now(timezone.utc) - timedelta(days=40))
    new = InterviewSession(owner_id="A")
    other = InterviewSession(owner_id="B",
                             created_at=datetime.now(timezone.utc) - timedelta(days=99))
    for s in (old, new, other):
        repo.create(s)
    deleted = purge_expired(repo, "A", retention_days=30)
    assert deleted == [old.id]
    assert repo.get(new.id, "A") is not None
    # B's expired session is untouched by A's purge.
    assert repo.get(other.id, "B") is not None
