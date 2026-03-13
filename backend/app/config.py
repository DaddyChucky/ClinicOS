from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from agents import set_default_openai_key
except Exception:  # pragma: no cover
    def set_default_openai_key(_: str) -> None:
        return None



REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
DEFAULT_SQLITE_PATH = BACKEND_ROOT / "clinic_copilot.db"
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
PRODUCTION_ENVIRONMENTS = {"production", "prod", "staging"}
LOCAL_ENVIRONMENTS = {"development", "dev", "local", "test", "testing"}


def _parse_env_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def is_postgres_url(database_url: str) -> bool:
    return database_url.startswith(("postgres://", "postgresql://", "postgresql+"))


def normalize_database_url(database_url: str) -> str:
    database_url = database_url.strip()
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


class Settings(BaseSettings):
    app_name: str = Field(default="ClinicOS API", validation_alias=AliasChoices("APP_NAME"))
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV", "NODE_ENV"),
    )
    database_url: str | None = Field(default=None, validation_alias=AliasChoices("DATABASE_URL"))
    local_sqlite_path: str = Field(
        default=str(DEFAULT_SQLITE_PATH),
        validation_alias=AliasChoices("LOCAL_SQLITE_PATH", "SQLITE_DATABASE_PATH"),
    )
    openai_api_key: str | None = Field(default=None, validation_alias=AliasChoices("OPENAI_API_KEY"))
    openai_model: str = Field(default="gpt-4.1-mini", validation_alias=AliasChoices("OPENAI_MODEL"))
    enable_marketing: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_MARKETING"))
    enable_live_sales_research: bool = Field(
        default=True,
        validation_alias=AliasChoices("ENABLE_LIVE_SALES_RESEARCH"),
    )
    live_research_timeout_seconds: int = Field(
        default=12,
        validation_alias=AliasChoices("LIVE_RESEARCH_TIMEOUT_SECONDS"),
    )
    cors_origins: str = Field(
        default=",".join(DEFAULT_CORS_ORIGINS),
        validation_alias=AliasChoices("CORS_ORIGINS", "ALLOWED_ORIGINS"),
    )
    frontend_url: str | None = Field(default=None, validation_alias=AliasChoices("FRONTEND_URL"))
    trusted_hosts: str = Field(
        default="",
        validation_alias=AliasChoices("TRUSTED_HOSTS"),
    )
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL"))
    auto_create_sqlite_schema: bool = Field(
        default=True,
        validation_alias=AliasChoices("AUTO_CREATE_SQLITE_SCHEMA"),
    )

    model_config = SettingsConfigDict(
        env_file=(
            str(REPO_ROOT / ".env"),
            str(BACKEND_ROOT / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: Any) -> str:
        text = str(value or "development").strip().lower()
        if text in {"prod", "production"}:
            return "production"
        if text in {"stage", "staging"}:
            return "staging"
        if text in {"dev", "development"}:
            return "development"
        return text or "development"

    @field_validator("database_url", "frontend_url", "openai_api_key", mode="before")
    @classmethod
    def blank_strings_to_none(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @property
    def is_production_like(self) -> bool:
        return self.environment in PRODUCTION_ENVIRONMENTS

    @property
    def sqlite_fallback_url(self) -> str:
        sqlite_path = Path(self.local_sqlite_path)
        if not sqlite_path.is_absolute():
            sqlite_path = BACKEND_ROOT / sqlite_path
        return f"sqlite:///{sqlite_path.resolve()}"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            database_url = normalize_database_url(self.database_url)
        else:
            if self.is_production_like:
                raise RuntimeError("DATABASE_URL must be set to a PostgreSQL connection string in production or staging.")
            database_url = self.sqlite_fallback_url

        if self.is_production_like and not is_postgres_url(database_url):
            raise RuntimeError("Production and staging environments must use PostgreSQL via DATABASE_URL.")
        return database_url

    @property
    def database_backend(self) -> str:
        return "sqlite" if is_sqlite_url(self.resolved_database_url) else "postgresql"

    @property
    def should_auto_create_schema(self) -> bool:
        return (
            self.auto_create_sqlite_schema
            and self.environment in LOCAL_ENVIRONMENTS
            and is_sqlite_url(self.resolved_database_url)
        )

    @property
    def cors_origin_list(self) -> list[str]:
        origins = _parse_env_list(self.cors_origins)
        if self.frontend_url:
            origins.append(self.frontend_url)

        cleaned: list[str] = []
        seen: set[str] = set()
        for origin in origins:
            normalized = origin.strip().rstrip("/")
            if not normalized:
                continue
            if normalized == "*":
                return ["*"]
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(normalized)
        return cleaned or list(DEFAULT_CORS_ORIGINS)

    @property
    def cors_allow_credentials(self) -> bool:
        return "*" not in self.cors_origin_list

    @property
    def trusted_host_list(self) -> list[str]:
        hosts: list[str] = []
        seen: set[str] = set()
        for host in _parse_env_list(self.trusted_hosts):
            normalized = host.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            hosts.append(normalized)
        return hosts


def configure_openai(settings: Settings | None = None) -> None:
    current = settings or get_settings()
    if current.openai_api_key:
        set_default_openai_key(current.openai_api_key)
    return None


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.openai_api_key:
        set_default_openai_key(settings.openai_api_key)
    return settings
