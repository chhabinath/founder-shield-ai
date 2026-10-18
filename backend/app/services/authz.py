"""Authorization / ownership enforcement.

Ownership is validated in backend code on every resource access. To avoid
resource enumeration (AD-5), a resource owned by someone else is reported
as NotFound rather than Forbidden — consistent with RLS making other
owners' rows invisible.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class NotAuthenticated(Exception):
    """No valid authenticated identity on the request."""


class ResourceNotFound(Exception):
    """Resource does not exist OR is not owned by the caller."""


@runtime_checkable
class Owned(Protocol):
    owner_id: str


def require_owner(resource: Owned | None, owner_id: str):
    """Return the resource iff it exists and is owned by `owner_id`.

    Missing resource and cross-owner access are indistinguishable to the
    caller (both -> ResourceNotFound) to prevent enumeration.
    """
    if resource is None or getattr(resource, "owner_id", None) != owner_id:
        raise ResourceNotFound()
    return resource
