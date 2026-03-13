from __future__ import annotations

import pytest

from app.config import BACKEND_ROOT, Settings


def test_settings_use_sqlite_fallback_in_local_mode(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None, environment="development", database_url=None, local_sqlite_path="clinic_copilot.db")

    assert settings.database_backend == "sqlite"
    assert settings.should_auto_create_schema is True
    assert settings.sqlite_fallback_url == f"sqlite:///{(BACKEND_ROOT / 'clinic_copilot.db').resolve()}"


def test_settings_require_postgres_in_production(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(
        _env_file=None,
        environment="production",
        database_url="postgresql://user:pass@db.example.com:5432/clinicos",
    )

    assert settings.is_production_like is True
    assert settings.database_backend == "postgresql"
    assert settings.resolved_database_url == "postgresql+psycopg://user:pass@db.example.com:5432/clinicos"

    with pytest.raises(RuntimeError):
        Settings(_env_file=None, environment="production", database_url=None).resolved_database_url


def test_settings_parse_cors_and_frontend_urls(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    settings = Settings(
        _env_file=None,
        environment="development",
        cors_origins="http://localhost:3000, https://clinic.example.com/ ",
        frontend_url="https://app.clinicos.com/",
    )

    assert settings.cors_origin_list == [
        "http://localhost:3000",
        "https://clinic.example.com",
        "https://app.clinicos.com",
    ]
    assert settings.cors_allow_credentials is True


def test_settings_allow_blank_openai_key_for_fallback_mode():
    settings = Settings(
        _env_file=None,
        environment="development",
        openai_api_key="",
    )

    assert settings.openai_api_key is None
    assert settings.enable_live_sales_research is True
