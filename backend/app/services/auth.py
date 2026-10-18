"""Authentication providers and the current-owner dependency.

Primary path: verify a Supabase-issued JWT (HS256) using SUPABASE_JWT_SECRET
and derive owner_id from the `sub` claim. The browser never asserts its own
identity; it is always derived from a verified token.

Dev path: a header-based identity is permitted ONLY when app_env != production
AND allow_dev_auth is explicitly true. It fails closed otherwise, so it can
never be used as a production authentication bypass.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import jwt  # PyJWT (documented library)
from pydantic import BaseModel

from app.config import Settings


class OwnerIdentity(BaseModel):
    owner_id: str
    email: str | None = None


class AuthError(Exception):
    """Authentication failed (missing/invalid/expired token)."""


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AuthError("empty bearer token")
    return token


class AuthProvider(ABC):
    @abstractmethod
    def authenticate(
        self, authorization: str | None, headers: dict[str, str] | None = None
    ) -> OwnerIdentity: ...


class SupabaseJwtAuthProvider(AuthProvider):
    """Verifies Supabase HS256 JWTs."""

    def __init__(self, jwt_secret: str, audience: str = "authenticated") -> None:
        if not jwt_secret:
            raise ValueError("jwt secret is required for SupabaseJwtAuthProvider")
        self._secret = jwt_secret
        self._audience = audience

    def authenticate(
        self, authorization: str | None, headers: dict[str, str] | None = None
    ) -> OwnerIdentity:
        token = _bearer_token(authorization)
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=["HS256"],
                audience=self._audience,
                options={"require": ["sub", "exp"]},
            )
        except jwt.PyJWTError as exc:  # expired, bad sig, missing claim, etc.
            raise AuthError("invalid token") from exc
        sub = claims.get("sub")
        if not sub:
            raise AuthError("token missing subject")
        return OwnerIdentity(owner_id=str(sub), email=claims.get("email"))


class DevAuthProvider(AuthProvider):
    """Header-based identity for local dev ONLY. Fails closed in production."""

    HEADER = "x-dev-owner-id"

    def __init__(self, enabled: bool) -> None:
        self._enabled = enabled

    def authenticate(
        self, authorization: str | None, headers: dict[str, str] | None = None
    ) -> OwnerIdentity:
        if not self._enabled:
            raise AuthError("dev auth disabled")
        headers = {k.lower(): v for k, v in (headers or {}).items()}
        owner_id = headers.get(self.HEADER)
        if not owner_id:
            raise AuthError("missing dev owner header")
        return OwnerIdentity(owner_id=owner_id, email=None)


def build_auth_provider(settings: Settings) -> AuthProvider:
    """Select the auth provider from validated settings.

    Precedence: a configured Supabase JWT secret wins. Otherwise, dev auth
    is allowed only in non-production with the explicit flag set; in all
    other cases we return a disabled dev provider that fails closed.
    """
    if settings.supabase_jwt_secret:
        return SupabaseJwtAuthProvider(settings.supabase_jwt_secret)
    dev_ok = (not settings.is_production) and settings.allow_dev_auth
    return DevAuthProvider(enabled=dev_ok)
