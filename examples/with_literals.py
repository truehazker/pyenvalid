"""Constrained values with Literal types."""

from typing import Literal

from pydantic_settings import BaseSettings

from pyenvalid import validate_settings


class Settings(BaseSettings):
    api_key: str
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


settings = validate_settings(Settings)
print(f"Running in {settings.environment} mode")
