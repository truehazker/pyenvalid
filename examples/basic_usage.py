"""Basic usage example."""

from pydantic_settings import BaseSettings

from pyenvalid import validate_settings


class Settings(BaseSettings):
    database_url: str
    api_key: str
    port: int = 8080


settings = validate_settings(Settings)
print(f"Connected to {settings.database_url}")
