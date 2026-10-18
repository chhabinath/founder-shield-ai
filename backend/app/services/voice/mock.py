"""Mock voice provider - fully functional end-to-end with no network.

Mints a fake short-lived client token and simulates session lifecycle so the
whole app can run and be tested without any real provider or credentials.
"""
import uuid

from app.schemas.voice import VoiceSessionRequest, VoiceSessionResult
from app.services.voice.base import VoiceProvider


class MockVoiceProvider(VoiceProvider):
    def __init__(self) -> None:
        self._active: set[str] = set()

    @property
    def name(self) -> str:
        return "mock"

    def start_session(self, request: VoiceSessionRequest) -> VoiceSessionResult:
        self._active.add(request.session_id)
        self._log("session_started", request.session_id, mode=request.mode.value)
        return VoiceSessionResult(
            provider=self.name,
            session_id=request.session_id,
            client_token=f"mock-token-{uuid.uuid4().hex[:12]}",
            connect_url="wss://mock.local/agent/connect",
            expires_in=30,
            input_audio_format="pcm_24000",
            output_audio_format="pcm_24000",
            status="ready",
        )

    def end_session(self, session_id: str) -> None:
        # Idempotent: ending an unknown/already-ended session is a no-op.
        self._active.discard(session_id)
        self._log("session_ended", session_id)
