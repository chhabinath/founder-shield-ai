"""Abstract repository interfaces.

These define the persistence contract. Phase 02 ships an in-memory
implementation (test double). A Supabase-backed implementation is added
when a project + credentials are available, behind the same interface.

Every read/mutate takes an explicit `owner_id`. Implementations MUST scope
all access by owner; cross-owner access returns None (-> ResourceNotFound
at the service layer), never another owner's row.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.domain import (
    ApprovalRecord,
    AuditEvent,
    BriefVersion,
    InterviewRecord,
    InterviewSession,
    Owner,
    ProblemBrief,
)


class OwnerRepository(ABC):
    @abstractmethod
    def create(self, owner: Owner) -> Owner: ...
    @abstractmethod
    def get(self, owner_id: str) -> Owner | None: ...
    @abstractmethod
    def get_by_email(self, email: str) -> Owner | None: ...


class SessionRepository(ABC):
    @abstractmethod
    def create(self, session: InterviewSession) -> InterviewSession: ...
    @abstractmethod
    def get(self, session_id: str, owner_id: str) -> InterviewSession | None: ...
    @abstractmethod
    def list_for_owner(self, owner_id: str) -> list[InterviewSession]: ...
    @abstractmethod
    def update(self, session: InterviewSession) -> InterviewSession: ...
    @abstractmethod
    def delete(self, session_id: str, owner_id: str) -> bool: ...


class InterviewRecordRepository(ABC):
    @abstractmethod
    def add(self, record: InterviewRecord) -> InterviewRecord: ...
    @abstractmethod
    def list_for_session(self, session_id: str, owner_id: str) -> list[InterviewRecord]: ...


class BriefRepository(ABC):
    @abstractmethod
    def create(self, brief: ProblemBrief) -> ProblemBrief: ...
    @abstractmethod
    def get(self, brief_id: str, owner_id: str) -> ProblemBrief | None: ...
    @abstractmethod
    def update(self, brief: ProblemBrief) -> ProblemBrief: ...


class BriefVersionRepository(ABC):
    @abstractmethod
    def add(self, version: BriefVersion) -> BriefVersion: ...
    @abstractmethod
    def get(self, version_id: str, owner_id: str) -> BriefVersion | None: ...
    @abstractmethod
    def list_for_brief(self, brief_id: str, owner_id: str) -> list[BriefVersion]: ...


class ApprovalRepository(ABC):
    @abstractmethod
    def add(self, approval: ApprovalRecord) -> ApprovalRecord: ...
    @abstractmethod
    def get_active_for_version(self, version_id: str, owner_id: str) -> ApprovalRecord | None: ...
    @abstractmethod
    def invalidate_for_brief(self, brief_id: str, owner_id: str, version_ids: list[str]) -> int: ...


class AuditRepository(ABC):
    @abstractmethod
    def add(self, event: AuditEvent) -> AuditEvent: ...
    @abstractmethod
    def list_for_owner(self, owner_id: str) -> list[AuditEvent]: ...
