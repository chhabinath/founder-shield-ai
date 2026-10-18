"""Voice provider interface, normalized errors, and a bounded-retry helper.

The interface is intentionally small and provider-agnostic:
  * start_session -> set up a session and (where applicable) mint a
    short-lived client token for the browser.
  * end_session   -> best-effort cleanup / cancellation (idempotent).

Providers normalize their own errors into VoiceProviderError(kind=...), so
callers never branch on provider-specific exceptions.
"""
import enum
import logging
from abc import ABC, abstractmethod

import httpx

from app.schemas.voice import VoiceSessionRequest, VoiceSessionResult

_logger = logging.getLogger("foundershield.voice")


class VoiceErrorKind(str, enum.Enum):
    TIMEOUT = "timeout"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "provider_unavailable"
    BAD_RESPONSE = "bad_response"
    UNKNOWN = "unknown"


class VoiceProviderError(Exception):
    def __init__(self, kind: VoiceErrorKind, message: str) -> None:
        # message is a safe, generic string. Never embed tokens/secrets.
        super().__init__(f"{kind.value}: {message}")
        self.kind = kind
        self.message = message


def status_to_kind(status_code: int) -> VoiceErrorKind:
    if status_code in (401, 403):
        return VoiceErrorKind.UNAUTHORIZED
    if status_code == 404:
        return VoiceErrorKind.NOT_FOUND
    if status_code in (429, 500, 502, 503, 504):
        return VoiceErrorKind.UNAVAILABLE
    return VoiceErrorKind.BAD_RESPONSE


def post_with_retries(
    client: httpx.Client,
    url: str,
    *,
    headers: dict,
    json: dict,
    max_retries: int,
) -> httpx.Response:
    """POST with bounded retries on transport errors only.

    Transport errors (timeouts, connect failures) are retried up to
    max_retries. HTTP status errors are NOT retried here; the caller maps
    them to a normalized VoiceProviderError.
    """
    attempt = 0
    while True:
        try:
            return client.post(url, headers=headers, json=json)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if attempt >= max_retries:
                raise VoiceProviderError(
                    VoiceErrorKind.TIMEOUT, "voice provider unreachable"
                ) from exc
            attempt += 1


class VoiceProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def start_session(self, request: VoiceSessionRequest) -> VoiceSessionResult: ...

    @abstractmethod
    def end_session(self, session_id: str) -> None: ...

    def _log(self, event: str, session_id: str, **safe_fields) -> None:
        # Redacted diagnostics: provider + session id + event only.
        # NEVER include client tokens, API keys, or transcript text.
        extra = " ".join(f"{k}={v}" for k, v in safe_fields.items())
        _logger.info("voice_%s provider=%s session=%s %s",
                     event, self.name, session_id, extra)
