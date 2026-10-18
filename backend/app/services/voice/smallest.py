"""Smallest AI voice provider (server-side token minting only).

VERIFIED against the official docs on 2026-10-18:
  POST https://api.smallest.ai/atoms/v1/conversation/register-call
  Authorization: Bearer <API_KEY>   (key stays server-side)
  body: {"agent_id": "...", "mode": "webcall"|"chat", "variables": {...}}
  -> {"status": true, "data": {"access_token", "expires_in",
      "input_audio_format", "output_audio_format"}}
Source: docs.smallest.ai/api-reference/voice-agents/realtime-agent/register-call

The returned access_token is short-lived (~30s) and single-use; the browser
opens the WebSocket itself using the official @smallest-ai/agent-sdk. We do
NOT implement or invent the WebSocket protocol server-side.

This class is UNVERIFIED against the live service (no credentials available).
Its request/response SHAPE is covered by tests using httpx.MockTransport.
"""
import httpx

from app.schemas.voice import VoiceSessionRequest, VoiceSessionResult
from app.services.voice.base import (
    VoiceProvider, VoiceProviderError, VoiceErrorKind,
    post_with_retries, status_to_kind,
)

_REGISTER_CALL_URL = "https://api.smallest.ai/atoms/v1/conversation/register-call"
_CONNECT_URL = "wss://api.smallest.ai/atoms/v1/agent/connect"


class SmallestVoiceProvider(VoiceProvider):
    def __init__(self, api_key: str, agent_id: str,
                 timeout_seconds: float = 10.0, max_retries: int = 2,
                 client: httpx.Client | None = None) -> None:
        if not api_key or not agent_id:
            raise ValueError("Smallest provider requires api_key and agent_id")
        self._api_key = api_key
        self._agent_id = agent_id
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        # Injected client enables offline testing via MockTransport.
        self._client = client or httpx.Client(timeout=timeout_seconds)

    @property
    def name(self) -> str:
        return "smallest"

    def start_session(self, request: VoiceSessionRequest) -> VoiceSessionResult:
        payload = {"agent_id": self._agent_id, "mode": request.mode.value}
        if request.variables:
            payload["variables"] = request.variables
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        resp = post_with_retries(
            self._client, _REGISTER_CALL_URL,
            headers=headers, json=payload, max_retries=self._max_retries,
        )
        if resp.status_code != 200:
            # Normalized, safe error - never echo the body (may carry detail).
            raise VoiceProviderError(
                status_to_kind(resp.status_code),
                f"register-call failed ({resp.status_code})",
            )
        try:
            body = resp.json()
            data = body["data"]
            token = data["access_token"]
        except (ValueError, KeyError, TypeError) as exc:
            raise VoiceProviderError(
                VoiceErrorKind.BAD_RESPONSE, "unexpected register-call response"
            ) from exc

        self._log("session_started", request.session_id, mode=request.mode.value)
        return VoiceSessionResult(
            provider=self.name,
            session_id=request.session_id,
            client_token=token,
            connect_url=_CONNECT_URL,
            expires_in=data.get("expires_in"),
            input_audio_format=data.get("input_audio_format"),
            output_audio_format=data.get("output_audio_format"),
            status="ready",
        )

    def end_session(self, session_id: str) -> None:
        # The browser SDK owns the WebSocket lifecycle; the short-lived token
        # simply expires. Server-side cleanup is a no-op diagnostic here.
        self._log("session_ended", session_id)
