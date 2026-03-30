# config/setting.py
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==============================
# Application Settings
# ==============================
class Settings(BaseSettings):
    """Application settings."""

    # Pydantic Settings config
    model_config = SettingsConfigDict(
        # project root .env
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",               # ignore unknown env vars
        env_nested_delimiter="__",    # POSTGRES__HOST -> settings.postgres.host
    )

    # ------------------------------
    # General
    # ------------------------------
    project: str = Field(
        default="KubeTriage",
        alias="PROJECT",
        description="The project name",
    )

    env: str = Field(
        default="dev",
        alias="ENV",
        description="Environment name (dev/staging/prod).",
    )

    debug: bool = Field(
        default=False,      # Safe default unless explicitly enable
        alias="DEBUG",
        description="Whether it is debug mode",
    )

    cors: str = Field(
        default="http://localhost,http://localhost:8000,http://localhost:8080",
        alias="CORS",
        description="Allowed CORS origins",
    )

    # ------------------------------
    # Anthropic
    # ------------------------------
    anthropic_api_key: str = Field(
        default="",
        alias="ANTHROPIC_API_KEY",
        description="Anthropic API key",
    )

    anthropic_model: str = Field(
        default="",
        alias="ANTHROPIC_MODEL",
        description="Anthropic model",
    )

    # ------------------------------
    # Email
    # ------------------------------
    smtp_host: str = Field(
        default="smtp.gmail.com",
        alias="SMTP_HOST",
        description="smtp host",
    )

    smtp_port: int = Field(
        default=465,
        alias="SMTP_PORT",
        description="smtp host",
    )

    smtp_user: str = Field(
        default="",
        alias="SMTP_USER",
        description="SMTP username / Gmail address",
    )

    smtp_password: str = Field(
        default="",
        alias="SMTP_PASSWORD",
        description="smtp password",
    )

    notify_to: str = Field(
        default="",
        alias="NOTIFY_TO",
        description="Recipient email address for triage notifications",
    )

    # ------------------------------
    # Performance tuning
    # ------------------------------
    pool_size: int = Field(
        default=5,
        alias="POOL_SIZE",
        description="Max persistent DB connections in the pool.",
    )

    max_overflow: int = Field(
        default=10,
        alias="MAX_OVERFLOW",
        description="Extra DB connections allowed beyond pool_size.",
    )

    workers: int = Field(
        default=1,
        alias="WORKER",
        description="The number of uvicorn workers.",
    )

    # ------------------------------
    # Logging controls
    # ------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level: DEBUG/INFO/WARNING/ERROR/CRITICAL.",
    )

    # enable access log
    access_log_enabled: bool = Field(
        default=False,  # no access log, prevents log explode volume
        alias="ACCESS_LOG_ENABLED",
        description="Enable Uvicorn access logs.",
    )

    # enable log to file
    log_to_file: bool = Field(
        default=False,  # no log to file, log to stdout/stderr for best practice
        alias="LOG_TO_FILE",
        description="Write rotated files (usually False for ECS/EKS).",
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        """Normalize LOG_LEVEL input to uppercase (e.g., 'warn' -> 'WARN' -> invalid)."""
        return str(v).strip().upper()

    @property
    def cors_list(self) -> list[str]:
        """Parsed list of CORS origins from the comma-separated string."""
        return [
            origin.strip()
            for origin in self.cors.split(",")
            if origin.strip()
        ]


# ==============================
# Settings loader (cached)
# ==============================
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get a cached Settings instance.
    """
    return Settings()
