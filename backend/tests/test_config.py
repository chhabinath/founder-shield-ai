import pytest
from pydantic import ValidationError

from app.config import Settings


def test_cors_origins_parsed_as_list():
    s = Settings(cors_allowed_origins="http://a.com, http://b.com")
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]


def test_invalid_env_rejected():
    with pytest.raises(ValidationError):
        Settings(app_env="staging")


def test_invalid_log_level_rejected():
    with pytest.raises(ValidationError):
        Settings(log_level="verbose")


def test_production_rejects_raw_transcripts():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        Settings(app_env="production", database_backend="supabase",
                 supabase_jwt_secret="x"*40, store_raw_transcripts=True)


def test_production_rejects_dev_auth():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        Settings(app_env="production", database_backend="supabase",
                 supabase_jwt_secret="x"*40, allow_dev_auth=True)


def test_production_requires_supabase_backend():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        Settings(app_env="production", database_backend="memory",
                 supabase_jwt_secret="x"*40)


def test_production_requires_jwt_secret():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        Settings(app_env="production", database_backend="supabase")


def test_production_valid_config_ok():
    s = Settings(app_env="production", database_backend="supabase",
                 supabase_jwt_secret="x"*40, allow_dev_auth=False,
                 store_raw_transcripts=False,
                 cors_allowed_origins="https://app.example.com")
    assert s.is_production
    assert s.database_backend == "supabase"
