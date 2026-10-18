from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.services.auth import (
    SupabaseJwtAuthProvider, DevAuthProvider, AuthError,
)

SECRET = "test-secret-value-at-least-32-bytes-long-xx"
AUD = "authenticated"


def _token(sub="user-123", exp_delta=timedelta(hours=1), **extra):
    payload = {
        "sub": sub,
        "aud": AUD,
        "exp": datetime.now(timezone.utc) + exp_delta,
        **extra,
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_valid_token_yields_owner():
    p = SupabaseJwtAuthProvider(SECRET)
    ident = p.authenticate(f"Bearer {_token(email='f@x.io')}")
    assert ident.owner_id == "user-123"
    assert ident.email == "f@x.io"


def test_expired_token_rejected():
    p = SupabaseJwtAuthProvider(SECRET)
    with pytest.raises(AuthError):
        p.authenticate(f"Bearer {_token(exp_delta=timedelta(hours=-1))}")


def test_bad_signature_rejected():
    p = SupabaseJwtAuthProvider(SECRET)
    forged = jwt.encode({"sub": "x", "aud": AUD,
                         "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                        "wrong-key", algorithm="HS256")
    with pytest.raises(AuthError):
        p.authenticate(f"Bearer {forged}")


def test_missing_bearer_rejected():
    p = SupabaseJwtAuthProvider(SECRET)
    with pytest.raises(AuthError):
        p.authenticate(None)
    with pytest.raises(AuthError):
        p.authenticate("Token abc")


def test_dev_auth_disabled_fails_closed():
    p = DevAuthProvider(enabled=False)
    with pytest.raises(AuthError):
        p.authenticate(None, {"x-dev-owner-id": "anyone"})


def test_dev_auth_enabled_reads_header():
    p = DevAuthProvider(enabled=True)
    ident = p.authenticate(None, {"X-Dev-Owner-Id": "dev-user"})
    assert ident.owner_id == "dev-user"
