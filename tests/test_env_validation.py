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


class TestComplexSettings:
    """Tests for complex settings configurations."""

    def test_settings_with_multiple_literal_fields(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle multiple Literal fields."""

        class MultiLiteralSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None, case_sensitive=False)
            env: Literal["dev", "staging", "prod"] = "dev"
            log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
            mode: Literal["read", "write", "read-write"] = "read"

        clean_env.setenv("ENV", "prod")
        clean_env.setenv("LOG_LEVEL", "ERROR")
        clean_env.setenv("MODE", "read-write")

        settings = validate_settings(MultiLiteralSettings)

        assert settings.env == "prod"
        assert settings.log_level == "ERROR"
        assert settings.mode == "read-write"

    def test_settings_with_mixed_required_and_optional(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle mix of required and optional fields."""

        class MixedSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            required1: str
            optional1: str = "default1"
            required2: int
            optional2: int = 42
            required3: bool
            optional3: bool = False

        clean_env.setenv("REQUIRED1", "value1")
        clean_env.setenv("REQUIRED2", "100")
        clean_env.setenv("REQUIRED3", "true")

        settings = validate_settings(MixedSettings)

        assert settings.required1 == "value1"
        assert settings.optional1 == "default1"
        assert settings.required2 == 100
        assert settings.optional2 == 42
        assert settings.required3 is True
        assert settings.optional3 is False

    def test_override_some_defaults(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should allow overriding some but not all defaults."""

        class PartialOverrideSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            field1: str = "default1"
            field2: str = "default2"
            field3: str = "default3"

        clean_env.setenv("FIELD2", "custom2")

        settings = validate_settings(PartialOverrideSettings)

        assert settings.field1 == "default1"
        assert settings.field2 == "custom2"
        assert settings.field3 == "default3"

    def test_empty_string_overrides_default(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should allow empty string to override non-empty default."""

        class EmptyOverrideSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: str = "default"

        clean_env.setenv("VALUE", "")

        settings = validate_settings(EmptyOverrideSettings)

        assert settings.value == ""

    def test_whitespace_string_values(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should preserve whitespace in string values."""

        class WhitespaceSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: str

        clean_env.setenv("VALUE", "  spaces  ")

        settings = validate_settings(WhitespaceSettings)

        assert settings.value == "  spaces  "


class TestNumericEdgeCases:
    """Tests for numeric type edge cases."""

    def test_large_integer_values(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle very large integer values."""

        class LargeIntSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            big_number: int

        clean_env.setenv("BIG_NUMBER", "9999999999999999999")

        settings = validate_settings(LargeIntSettings)

        assert settings.big_number == 9999999999999999999

    def test_negative_float_values(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle negative float values."""

        class NegativeFloatSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: float

        clean_env.setenv("VALUE", "-3.14159")

        settings = validate_settings(NegativeFloatSettings)

        assert settings.value == -3.14159

    def test_integer_overflow_becomes_error(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle integer-like strings that aren't valid."""

        class IntSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: int

        clean_env.setenv("VALUE", "12.34")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(IntSettings)

        error = exc_info.value
        assert "value" in error.missing_fields

    def test_special_float_values(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle special float string formats."""

        class SpecialFloatSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: float

        # Test with leading zero
        clean_env.setenv("VALUE", "0.5")
        settings = validate_settings(SpecialFloatSettings)
        assert settings.value == 0.5

        # Test without leading zero
        clean_env.setenv("VALUE", ".5")
        settings = validate_settings(SpecialFloatSettings)
        assert settings.value == 0.5


class TestBooleanEdgeCases:
    """Additional tests for boolean conversion edge cases."""

    class StrictBoolSettings(BaseSettings):
        model_config = SettingsConfigDict(env_file=None)
        flag: bool

    def test_boolean_with_whitespace_fails(self, clean_env: pytest.MonkeyPatch) -> None:
        """Pydantic doesn't strip whitespace from boolean values."""
        clean_env.setenv("FLAG", " true ")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(self.StrictBoolSettings)

        assert "flag" in exc_info.value.missing_fields

    def test_numeric_one_as_true(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should convert numeric 1 to True."""
        clean_env.setenv("FLAG", "1")

        settings = validate_settings(self.StrictBoolSettings)

        assert settings.flag is True

    def test_numeric_zero_as_false(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should convert numeric 0 to False."""
        clean_env.setenv("FLAG", "0")

        settings = validate_settings(self.StrictBoolSettings)

        assert settings.flag is False


class TestErrorMessageQuality:
    """Tests for error message quality and content."""

    def test_missing_required_shows_helpful_message(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Error message should be helpful for missing required fields."""

        class HelpfulSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_key: str = Field(..., description="API key for authentication")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(HelpfulSettings)

        message = str(exc_info.value)

        # Should contain field name
        assert "API_KEY" in message
        # Should indicate it's missing
        assert "missing" in message
        # Should have helpful formatting
        assert "environment" in message.lower()

    def test_type_error_shows_error_type(self, clean_env: pytest.MonkeyPatch) -> None:
        """Error message should show the error type for type mismatches."""

        class TypeSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            count: int

        clean_env.setenv("COUNT", "not-a-number")

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(TypeSettings)

        error = exc_info.value
        message = str(error)

        # Should show the error type
        assert "int_parsing" in message
        # Should show field name
        assert "COUNT" in message


class TestRealWorldScenarios:
    """Tests simulating real-world configuration scenarios."""

    def test_database_configuration(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle typical database configuration."""

        class DatabaseSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            db_host: str = "localhost"
            db_port: int = 5432
            db_name: str
            db_user: str
            db_password: str
            db_ssl: bool = False

        clean_env.setenv("DB_NAME", "myapp")
        clean_env.setenv("DB_USER", "dbuser")
        clean_env.setenv("DB_PASSWORD", "secret123")
        clean_env.setenv("DB_PORT", "3306")
        clean_env.setenv("DB_SSL", "true")

        settings = validate_settings(DatabaseSettings)

        assert settings.db_host == "localhost"
        assert settings.db_port == 3306
        assert settings.db_name == "myapp"
        assert settings.db_user == "dbuser"
        assert settings.db_password == "secret123"
        assert settings.db_ssl is True

    def test_api_configuration(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle typical API configuration."""

        class ApiSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_url: str
            api_key: str
            api_timeout: int = 30
            api_retries: int = 3
            api_version: str = "v1"

        clean_env.setenv("API_URL", "https://api.example.com")
        clean_env.setenv("API_KEY", "sk_test_123456")
        clean_env.setenv("API_TIMEOUT", "60")

        settings = validate_settings(ApiSettings)

        assert settings.api_url == "https://api.example.com"
        assert settings.api_key == "sk_test_123456"
        assert settings.api_timeout == 60
        assert settings.api_retries == 3
        assert settings.api_version == "v1"

    def test_logging_configuration(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle typical logging configuration."""

        class LoggingSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
            log_format: str = "json"
            log_file: str = ""

        clean_env.setenv("LOG_LEVEL", "DEBUG")
        clean_env.setenv("LOG_FILE", "/var/log/app.log")

        settings = validate_settings(LoggingSettings)

        assert settings.log_level == "DEBUG"
        assert settings.log_format == "json"
        assert settings.log_file == "/var/log/app.log"

    def test_feature_flags_configuration(self, clean_env: pytest.MonkeyPatch) -> None:
        """Should handle feature flags configuration."""

        class FeatureFlagsSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            feature_new_ui: bool = False
            feature_beta_api: bool = False
            feature_analytics: bool = True

        clean_env.setenv("FEATURE_NEW_UI", "true")
        clean_env.setenv("FEATURE_BETA_API", "1")

        settings = validate_settings(FeatureFlagsSettings)

        assert settings.feature_new_ui is True
        assert settings.feature_beta_api is True
        assert settings.feature_analytics is True

    def test_missing_critical_database_config(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should fail gracefully when critical config is missing."""

        class CriticalDbSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            database_url: str
            database_password: str

        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(CriticalDbSettings)

        error = exc_info.value
        assert len(error.missing_fields) == 2
        assert "database_url" in error.missing_fields
        assert "database_password" in error.missing_fields

        # Error message should be clear
        message = str(error)
        assert "DATABASE_URL" in message
        assert "DATABASE_PASSWORD" in message
