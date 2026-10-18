"""Voice adapter data contracts (provider-independent).

No `from __future__ import annotations` (Pydantic resolves eagerly, matching
the rest of app/schemas). These types are normalized across providers so the
interview engine and API layer never see provider-specific shapes.
"""
import enum

from pydantic import BaseModel, Field


class VoiceSessionMode(str, enum.Enum):
    WEBCALL = "webcall"   # full voice pipeline (audio in + audio out)
    CHAT = "chat"         # text-only pipeline


class VoiceEventType(str, enum.Enum):
    SESSION_READY = "session_ready"
    TRANSCRIPT = "transcript"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    SESSION_ENDED = "session_ended"


class VoiceSessionRequest(BaseModel):
    session_id: str
    owner_id: str
    mode: VoiceSessionMode = VoiceSessionMode.WEBCALL
    locale: str = "en"
    # Per-call, non-sensitive prompt variables only. Never secrets.
    variables: dict = Field(default_factory=dict)


class VoiceSessionResult(BaseModel):
    provider: str
    session_id: str
    # Short-lived, single-use client token handed to the browser. NOT our
    # API key. Never logged. May be None if the provider uses another flow.
    client_token: str | None = None
    connect_url: str | None = None
    expires_in: int | None = None
    input_audio_format: str | None = None
    output_audio_format: str | None = None
    status: str = "ready"


class VoiceEvent(BaseModel):
    type: VoiceEventType
    session_id: str
    # Payload carries normalized, non-sensitive data only (e.g. transcript
    # text that will itself be redacted by the privacy guard before storage).
    data: dict = Field(default_factory=dict)
