"""Validated application settings (environment-driven).

All configuration comes from environment variables (or a local .env file
that must never be committed). No secrets are hardcoded here.
"""
from __future__ import annotations

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ALLOWED_ENVS = {"development", "test", "production"}
_ALLOWED_LEVELS = {"debug", "info", "warning", "error", "critical"}
_ALLOWED_DB_BACKENDS = {"memory", "supabase"}


class Settings(BaseSettings):
    """Application settings loaded and validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "FounderShield AI"
    api_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "info"
    # Explicit, comma-separated allowlist. No wildcards in production.
    cors_allowed_origins: str = "http://localhost:5173"

    # ---- Persistence / Supabase (Phase 02) ----
    # Default to the in-memory backend so local dev needs no credentials.
    database_backend: str = "memory"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None

    # Dev-only header auth. MUST remain false in production.
    allow_dev_auth: bool = False

    # ---- Retention (Phase 02/03) ----
    interview_retention_days: int = 30
    store_raw_transcripts: bool = False

    # ---- Voice provider (Phase 05) ----
    # mock by default so local dev needs no credentials.
    voice_provider: str = "mock"   # mock | smallest (verified) | bolna | sarvam
    voice_api_key: str | None = None
    voice_agent_id: str | None = None

    # ---- Reasoning / LLM provider (Phase 06) ----
    # mock by default so local dev / tests need no credentials.
    llm_provider: str = "mock"     # mock | <real-provider-id>
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_max_output_tokens: int = 2048

    @field_validator("app_env")
    @classmethod
    def _validate_env(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in _ALLOWED_ENVS:
            raise ValueError(f"app_env must be one of {sorted(_ALLOWED_ENVS)}")
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_level(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in _ALLOWED_LEVELS:
            raise ValueError(f"log_level must be one of {sorted(_ALLOWED_LEVELS)}")
        return v

    @field_validator("database_backend")
    @classmethod
    def _validate_backend(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in _ALLOWED_DB_BACKENDS:
            raise ValueError(f"database_backend must be one of {sorted(_ALLOWED_DB_BACKENDS)}")
        return v

    @model_validator(mode="after")
    def _production_safety(self) -> "Settings":
        # Security-critical invariants that must hold in production.
        if self.app_env == "production":
            if self.store_raw_transcripts:
                raise ValueError("store_raw_transcripts must be false in production")
            if self.allow_dev_auth:
                raise ValueError("allow_dev_auth must be false in production")
            if self.database_backend != "supabase":
                raise ValueError("production requires database_backend=supabase")
            if not self.supabase_jwt_secret:
                raise ValueError("production requires supabase_jwt_secret")
            if self.voice_provider not in ("mock",) and not (self.voice_api_key and self.voice_agent_id):
                raise ValueError("configured voice_provider requires voice_api_key and voice_agent_id")
            if self.llm_provider not in ("mock",) and not (self.llm_api_key and self.llm_model):
                raise ValueError("configured llm_provider requires llm_api_key and llm_model")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


_settings: Settings | None = None


def get_settings() -> "Settings":
    """Return a cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings