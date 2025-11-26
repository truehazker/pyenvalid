"""Load settings from .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict

from pyenvalid import validate_settings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    secret_key: str
    database_url: str


settings = validate_settings(Settings)
