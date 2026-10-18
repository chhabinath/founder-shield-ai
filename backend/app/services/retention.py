"""Retention & deletion policy helpers.

- No raw audio is stored (not modelled). Interview answer text is redacted.
- Redacted interview records are retained for a bounded window
  (INTERVIEW_RETENTION_DAYS); the owner may delete at any time.
- Deletion is owner-scoped and cascades to a session's dependent records.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.repositories.base import (
    InterviewRecordRepository,
    SessionRepository,
)


def cutoff(now: datetime | None, retention_days: int) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now - timedelta(days=retention_days)


def purge_expired(
    sessions: SessionRepository,
    owner_id: str,
    retention_days: int,
    now: datetime | None = None,
) -> list[str]:
    """Delete the owner's sessions older than the retention window.

    Returns the list of deleted session ids. Operates only within the
    caller's own data.
    """
    limit = cutoff(now, retention_days)
    deleted: list[str] = []
    for s in sessions.list_for_owner(owner_id):
        if s.created_at < limit:
            if sessions.delete(s.id, owner_id):
                deleted.append(s.id)
    return deleted
