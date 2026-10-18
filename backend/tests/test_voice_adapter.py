"""Phase 05 voice-adapter tests. Mock provider + verified Smallest request
shape via httpx.MockTransport (no network, no credentials)."""
import httpx
import pytest

from app.schemas.voice import VoiceSessionRequest, VoiceSessionMode
from app.services.voice.mock import MockVoiceProvider
from app.services.voice.smallest import SmallestVoiceProvider
from app.services.voice.base import (
    VoiceProviderError, VoiceErrorKind, status_to_kind,
)


def _req(owner="owner-A", sid="sess-1", mode=VoiceSessionMode.WEBCALL):
    return VoiceSessionRequest(session_id=sid, owner_id=owner, mode=mode)


# ---- mock provider ----
def test_mock_start_returns_token_and_is_ready():
    p = MockVoiceProvider()
    res = p.start_session(_req())
    assert res.provider == "mock"
    assert res.client_token and res.client_token.startswith("mock-token-")
    assert res.status == "ready"
    assert res.expires_in == 30


def test_mock_end_is_idempotent():
    p = MockVoiceProvider()
    p.start_session(_req(sid="s9"))
    p.end_session("s9")
    p.end_session("s9")  # no raise on repeat
    p.end_session("never-existed")  # no raise on unknown


# ---- Smallest provider: verified request shape, mocked transport ----
def _smallest_with(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return SmallestVoiceProvider(api_key="server-side-key",
                                 agent_id="agent-xyz", client=client)


def test_smallest_builds_documented_request_and_parses_token():
    seen = {}

    def handler(request):
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization", "")
        import json
        seen["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json={"status": True, "data": {
            "access_token": "wct_abc123", "expires_in": 30,
            "input_audio_format": "pcm_24000",
            "output_audio_format": "pcm_24000"}})

    p = _smallest_with(handler)
    res = p.start_session(_req())
    # request matches the verified docs exactly
    assert seen["method"] == "POST"
    assert seen["url"] == "https://api.smallest.ai/atoms/v1/conversation/register-call"
    assert seen["auth"].startswith("Bearer ")
    assert seen["body"]["agent_id"] == "agent-xyz"
    assert seen["body"]["mode"] == "webcall"
    # response parsed into normalized result
    assert res.client_token == "wct_abc123"
    assert res.expires_in == 30
    assert res.connect_url.startswith("wss://api.smallest.ai")


def test_smallest_api_key_never_in_result():
    def handler(request):
        return httpx.Response(200, json={"status": True, "data": {
            "access_token": "wct_abc123", "expires_in": 30}})
    p = _smallest_with(handler)
    res = p.start_session(_req())
    # The server-side API key must never leak into the browser-facing result.
    assert "server-side-key" not in res.model_dump_json()


def test_smallest_unauthorized_maps_to_error():
    def handler(request):
        return httpx.Response(401, json={"error": "bad key"})
    p = _smallest_with(handler)
    with pytest.raises(VoiceProviderError) as ei:
        p.start_session(_req())
    assert ei.value.kind == VoiceErrorKind.UNAUTHORIZED


def test_smallest_500_maps_to_unavailable():
    def handler(request):
        return httpx.Response(503, text="down")
    p = _smallest_with(handler)
    with pytest.raises(VoiceProviderError) as ei:
        p.start_session(_req())
    assert ei.value.kind == VoiceErrorKind.UNAVAILABLE


def test_smallest_bad_body_maps_to_bad_response():
    def handler(request):
        return httpx.Response(200, json={"status": True})  # missing 'data'
    p = _smallest_with(handler)
    with pytest.raises(VoiceProviderError) as ei:
        p.start_session(_req())
    assert ei.value.kind == VoiceErrorKind.BAD_RESPONSE


def test_smallest_timeout_retries_then_normalizes():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        raise httpx.ConnectTimeout("boom")

    p = _smallest_with(handler)
    with pytest.raises(VoiceProviderError) as ei:
        p.start_session(_req())
    assert ei.value.kind == VoiceErrorKind.TIMEOUT
    # initial attempt + 2 retries = 3 calls
    assert calls["n"] == 3


def test_smallest_requires_credentials():
    with pytest.raises(ValueError):
        SmallestVoiceProvider(api_key="", agent_id="")


def test_status_to_kind_mapping():
    assert status_to_kind(401) == VoiceErrorKind.UNAUTHORIZED
    assert status_to_kind(404) == VoiceErrorKind.NOT_FOUND
    assert status_to_kind(503) == VoiceErrorKind.UNAVAILABLE
    assert status_to_kind(418) == VoiceErrorKind.BAD_RESPONSE


# ---- factory selection ----
def test_factory_defaults_to_mock():
    from app.services.voice.factory import build_voice_provider

    class S:
        voice_provider = "mock"
        voice_api_key = None
        voice_agent_id = None
    assert build_voice_provider(S()).name == "mock"


def test_factory_smallest_without_creds_falls_back_to_mock():
    from app.services.voice.factory import build_voice_provider

    class S:
        voice_provider = "smallest"
        voice_api_key = None
        voice_agent_id = None
    # Fail safe in dev: no creds -> mock, never a broken real provider.
    assert build_voice_provider(S()).name == "mock"


def test_factory_smallest_with_creds_selects_smallest():
    from app.services.voice.factory import build_voice_provider

    class S:
        voice_provider = "smallest"
        voice_api_key = "k"
        voice_agent_id = "a"
    assert build_voice_provider(S()).name == "smallest"
