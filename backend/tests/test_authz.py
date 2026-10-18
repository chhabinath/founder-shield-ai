import pytest

from app.schemas.domain import InterviewSession
from app.services.authz import require_owner, ResourceNotFound


def test_owner_can_access_own_resource():
    s = InterviewSession(owner_id="owner-A")
    assert require_owner(s, "owner-A") is s


def test_cross_owner_access_is_not_found():
    s = InterviewSession(owner_id="owner-A")
    with pytest.raises(ResourceNotFound):
        require_owner(s, "owner-B")


def test_missing_resource_is_not_found():
    with pytest.raises(ResourceNotFound):
        require_owner(None, "owner-A")
