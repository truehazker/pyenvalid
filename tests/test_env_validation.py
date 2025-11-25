"""Integration tests for environment variable validation scenarios."""

from typing import Literal

import pytest
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from pyenvalid import ConfigurationError, validate_settings


class ProductionSettings(BaseSettings):
    """Realistic production settings class."""

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
        extra="ignore",
    )

    # Required - no defaults
    database_url: str = Field(..., description="PostgreSQL connection string")
    secret_key: str = Field(..., description="Application secret key")
    redis_url: str = Field(..., description="Redis connection string")

    # Optional with defaults
    app_name: str = Field(default="myapp", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)
    workers: int = Field(default=4)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")


class TestEnvironmentValidation:
    """Integration tests for full environment validation scenarios."""

    def test_all_required_missing(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should fail when all required fields are missing."""
        _ = clean_env  # Ensures clean environment
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ProductionSettings)

        error = exc_info.value
        assert len(error.missing_fields) == 3
        assert "database_url" in error.missing_fields
        assert "secret_key" in error.missing_fields
        assert "redis_url" in error.missing_fields

    def test_partial_required_missing(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should fail when some required fields are missing."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ProductionSettings)

        error = exc_info.value
        assert len(error.missing_fields) == 2
        assert "database_url" not in error.missing_fields
        assert "secret_key" in error.missing_fields
        assert "redis_url" in error.missing_fields

    def test_all_required_present(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should succeed when all required fields are set."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")
        clean_env.setenv("SECRET_KEY", "super-secret-key")
        clean_env.setenv("REDIS_URL", "redis://localhost:6379")

        settings = validate_settings(ProductionSettings)

        assert settings.database_url == "postgres://localhost/db"
        assert settings.secret_key == "super-secret-key"
        assert settings.redis_url == "redis://localhost:6379"
        # Defaults should be applied
        assert settings.app_name == "myapp"
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.workers == 4
        assert settings.log_level == "INFO"

    def test_override_defaults(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should allow overriding default values."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")
        clean_env.setenv("SECRET_KEY", "super-secret-key")
        clean_env.setenv("REDIS_URL", "redis://localhost:6379")
        clean_env.setenv("ENVIRONMENT", "production")
        clean_env.setenv("DEBUG", "false")
        clean_env.setenv("WORKERS", "8")
        clean_env.setenv("LOG_LEVEL", "WARNING")

        settings = validate_settings(ProductionSettings)

        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.workers == 8
        assert settings.log_level == "WARNING"

    def test_case_insensitive_env_vars(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle mixed case environment variable names."""
        clean_env.setenv("database_url", "postgres://localhost/db")
        clean_env.setenv("SECRET_KEY", "super-secret-key")
        clean_env.setenv("Redis_Url", "redis://localhost:6379")

        settings = validate_settings(ProductionSettings)

        assert settings.database_url == "postgres://localhost/db"
        assert settings.secret_key == "super-secret-key"
        assert settings.redis_url == "redis://localhost:6379"

    def test_invalid_integer_type(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should report type error for invalid integer."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")
        clean_env.setenv("SECRET_KEY", "super-secret-key")
        clean_env.setenv("REDIS_URL", "redis://localhost:6379")
        clean_env.setenv("WORKERS", "not-a-number")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ProductionSettings)

        error = exc_info.value
        assert "workers" in error.missing_fields
        workers_error = next(
            (err_type for field, err_type in error.errors if field == "workers"), None
        )
        assert workers_error == "int_parsing"

    def test_invalid_boolean_type(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should report type error for invalid boolean."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")
        clean_env.setenv("SECRET_KEY", "super-secret-key")
        clean_env.setenv("REDIS_URL", "redis://localhost:6379")
        clean_env.setenv("DEBUG", "not-a-bool")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ProductionSettings)

        error = exc_info.value
        assert "debug" in error.missing_fields

    def test_invalid_literal_value(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should report error for invalid literal choice."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")
        clean_env.setenv("SECRET_KEY", "super-secret-key")
        clean_env.setenv("REDIS_URL", "redis://localhost:6379")
        clean_env.setenv("ENVIRONMENT", "invalid-env")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ProductionSettings)

        error = exc_info.value
        assert "environment" in error.missing_fields
        env_error = next(
            (err_type for field, err_type in error.errors if field == "environment"),
            None,
        )
        assert env_error == "literal_error"

    def test_multiple_validation_errors(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should report all validation errors at once."""
        clean_env.setenv("DATABASE_URL", "postgres://localhost/db")
        # Missing: SECRET_KEY, REDIS_URL
        clean_env.setenv("WORKERS", "not-a-number")  # Invalid type
        clean_env.setenv("ENVIRONMENT", "invalid")  # Invalid literal

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ProductionSettings)

        error = exc_info.value
        # Should have all 4 errors
        assert len(error.missing_fields) == 4
        assert "secret_key" in error.missing_fields
        assert "redis_url" in error.missing_fields
        assert "workers" in error.missing_fields
        assert "environment" in error.missing_fields


class TestBooleanConversion:
    """Tests for boolean environment variable conversion."""

    class BoolSettings(BaseSettings):
        model_config = SettingsConfigDict(env_file=None)
        flag: bool = False

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ],
    )
    def test_boolean_conversion(
        self,
        clean_env: pytest.MonkeyPatch,
        value: str,
        expected: bool,
    ) -> None:
        """Should convert various string values to boolean."""
        clean_env.setenv("FLAG", value)

        settings = validate_settings(self.BoolSettings)

        assert settings.flag is expected
