"""Select the voice provider from validated server-side settings.

Defaults to the mock provider so local dev needs no credentials. A real
provider is only constructed when explicitly configured AND its required
settings are present; otherwise we fail safe to mock (non-production) or
raise (production misconfiguration is caught at config load, see config.py).
"""
import logging

from app.services.voice.base import VoiceProvider
from app.services.voice.mock import MockVoiceProvider
from app.services.voice.smallest import SmallestVoiceProvider

_logger = logging.getLogger("foundershield.voice")


def build_voice_provider(settings) -> VoiceProvider:
    provider = (settings.voice_provider or "mock").lower()

    if provider == "mock":
        return MockVoiceProvider()

    if provider == "smallest":
        if not settings.voice_api_key or not settings.voice_agent_id:
            # Fail safe in non-production; config validation blocks prod.
            _logger.info("voice_provider_fallback reason=missing_smallest_config")
            return MockVoiceProvider()
        return SmallestVoiceProvider(
            api_key=settings.voice_api_key,
            agent_id=settings.voice_agent_id,
        )

    # Unknown provider id -> safe default.
    _logger.info("voice_provider_fallback reason=unknown_provider")
    return MockVoiceProvider()
