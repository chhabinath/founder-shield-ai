"""In-memory repository implementations (local dev / test doubles).

Ownership is enforced in every method: a lookup that does not match the
caller's owner_id returns None (or False for deletes), never another
owner's data. This mirrors the behaviour RLS enforces in Postgres.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.domain import (
    ApprovalRecord,
    ApprovalStatus,
    AuditEvent,
    BriefVersion,
    InterviewRecord,
    InterviewSession,
    Owner,
    ProblemBrief,
)
from app.repositories.base import (
    ApprovalRepository,
    AuditRepository,
    BriefRepository,
    BriefVersionRepository,
    InterviewRecordRepository,
    OwnerRepository,
    SessionRepository,
)


class InMemoryOwnerRepository(OwnerRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, Owner] = {}

    def create(self, owner: Owner) -> Owner:
        self._by_id[owner.id] = owner
        return owner

    def get(self, owner_id: str) -> Owner | None:
        return self._by_id.get(owner_id)

    def get_by_email(self, email: str) -> Owner | None:
        return next((o for o in self._by_id.values() if o.email == email), None)


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, InterviewSession] = {}

    def create(self, session: InterviewSession) -> InterviewSession:
        self._by_id[session.id] = session
        return session

    def get(self, session_id: str, owner_id: str) -> InterviewSession | None:
        s = self._by_id.get(session_id)
        return s if s and s.owner_id == owner_id else None

    def list_for_owner(self, owner_id: str) -> list[InterviewSession]:
        return [s for s in self._by_id.values() if s.owner_id == owner_id]

    def update(self, session: InterviewSession) -> InterviewSession:
        existing = self._by_id.get(session.id)
        if not existing or existing.owner_id != session.owner_id:
            raise KeyError("session not found for owner")
        session.updated_at = datetime.now(timezone.utc)
        self._by_id[session.id] = session
        return session

    def delete(self, session_id: str, owner_id: str) -> bool:
        s = self._by_id.get(session_id)
        if s and s.owner_id == owner_id:
            del self._by_id[session_id]
            return True
        return False


class InMemoryInterviewRecordRepository(InterviewRecordRepository):
    def __init__(self) -> None:
        self._items: list[InterviewRecord] = []

    def add(self, record: InterviewRecord) -> InterviewRecord:
        self._items.append(record)
        return record

    def list_for_session(self, session_id: str, owner_id: str) -> list[InterviewRecord]:
        return [
            r for r in self._items
            if r.session_id == session_id and r.owner_id == owner_id
        ]


class InMemoryBriefRepository(BriefRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, ProblemBrief] = {}

    def create(self, brief: ProblemBrief) -> ProblemBrief:
        self._by_id[brief.id] = brief
        return brief

    def get(self, brief_id: str, owner_id: str) -> ProblemBrief | None:
        b = self._by_id.get(brief_id)
        return b if b and b.owner_id == owner_id else None

    def update(self, brief: ProblemBrief) -> ProblemBrief:
        existing = self._by_id.get(brief.id)
        if not existing or existing.owner_id != brief.owner_id:
            raise KeyError("brief not found for owner")
        self._by_id[brief.id] = brief
        return brief


class InMemoryBriefVersionRepository(BriefVersionRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, BriefVersion] = {}

    def add(self, version: BriefVersion) -> BriefVersion:
        self._by_id[version.id] = version
        return version

    def get(self, version_id: str, owner_id: str) -> BriefVersion | None:
        v = self._by_id.get(version_id)
        return v if v and v.owner_id == owner_id else None

    def list_for_brief(self, brief_id: str, owner_id: str) -> list[BriefVersion]:
        return sorted(
            [v for v in self._by_id.values()
             if v.brief_id == brief_id and v.owner_id == owner_id],
            key=lambda v: v.version_number,
        )


class InMemoryApprovalRepository(ApprovalRepository):
    def __init__(self) -> None:
        self._by_id: dict[str, ApprovalRecord] = {}

    def add(self, approval: ApprovalRecord) -> ApprovalRecord:
        self._by_id[approval.id] = approval
        return approval

    def get_active_for_version(self, version_id: str, owner_id: str) -> ApprovalRecord | None:
        return next(
            (a for a in self._by_id.values()
             if a.brief_version_id == version_id
             and a.owner_id == owner_id
             and a.status == ApprovalStatus.ACTIVE),
            None,
        )

    def invalidate_for_brief(self, brief_id: str, owner_id: str, version_ids: list[str]) -> int:
        count = 0
        for a in self._by_id.values():
            if (a.owner_id == owner_id
                    and a.brief_version_id in version_ids
                    and a.status == ApprovalStatus.ACTIVE):
                a.status = ApprovalStatus.INVALIDATED
                a.invalidated_at = datetime.now(timezone.utc)
                count += 1
        return count


class InMemoryAuditRepository(AuditRepository):
    def __init__(self) -> None:
        self._items: list[AuditEvent] = []

    def add(self, event: AuditEvent) -> AuditEvent:
        self._items.append(event)
        return event

    def list_for_owner(self, owner_id: str) -> list[AuditEvent]:
        return [e for e in self._items if e.owner_id == owner_id]
