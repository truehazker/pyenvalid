"""Pyenvalid - Beautiful validation errors for pydantic-settings.

A lightweight library that provides user-friendly error messages when
environment variable validation fails in pydantic-settings applications.

Example:
    >>> from pydantic_settings import BaseSettings
    >>> from pyenvalid import validate_settings, ConfigurationError
    >>>
    >>> class Settings(BaseSettings):
    ...     api_key: str
    ...     database_url: str
    ...     port: int = 8080
    >>>
    >>> try:
    ...     settings = validate_settings(Settings)
    ... except ConfigurationError as e:
    ...     print(e)  # Beautiful formatted error
"""

from pyenvalid.validation import ConfigurationError, validate_settings

__all__ = ["ConfigurationError", "validate_settings"]
