"""Pytest configuration and fixtures."""

from typing import Literal

import pytest
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SimpleSettings(BaseSettings):
    """Simple settings with required and optional fields."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    required_field: str
    optional_field: str = "default_value"


class MultiFieldSettings(BaseSettings):
    """Settings with multiple required fields of different types."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(..., description="Database connection URL")
    api_key: str = Field(..., description="API key")
    port: int = Field(..., description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Log level"
    )


class AllDefaultsSettings(BaseSettings):
    """Settings where all fields have defaults."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    host: str = "localhost"
    port: int = 8080
    debug: bool = False


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Fixture that clears common test environment variables."""
    env_vars = [
        "REQUIRED_FIELD",
        "OPTIONAL_FIELD",
        "DATABASE_URL",
        "API_KEY",
        "PORT",
        "DEBUG",
        "LOG_LEVEL",
        "HOST",
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch

