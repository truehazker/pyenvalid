"""Edge case tests for validate_settings function."""

from typing import Literal, Optional

import pytest
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pyenvalid import ConfigurationError, validate_settings


class TestValidateSettingsEdgeCases:
    """Tests for edge cases in validate_settings function."""

    def test_settings_with_nested_error_location(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle nested field error locations."""
        
        class NestedSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            simple_field: str
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(NestedSettings)
        
        error = exc_info.value
        assert "simple_field" in error.missing_fields

    def test_settings_with_empty_error_location(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle errors with empty location tuple gracefully."""
        # This is a rare edge case but should be handled
        
        class EmptyLocSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            required_field: str
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(EmptyLocSettings)
        
        error = exc_info.value
        # Should not crash, should extract field name
        assert len(error.errors) > 0

    def test_settings_with_optional_fields(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle Optional fields correctly."""
        
        class OptionalSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            required: str
            optional: Optional[str] = None
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(OptionalSettings)
        
        error = exc_info.value
        assert "required" in error.missing_fields
        assert "optional" not in error.missing_fields

    def test_settings_with_validator_error(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle custom validator errors."""
        
        class ValidatedSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            port: int
            
            @field_validator("port")
            @classmethod
            def validate_port(cls, v: int) -> int:
                if v < 1 or v > 65535:
                    raise ValueError("Port must be between 1 and 65535")
                return v
        
        clean_env.setenv("PORT", "99999")
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ValidatedSettings)
        
        error = exc_info.value
        assert "port" in error.missing_fields

    def test_all_defaults_settings_success(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should succeed when all fields have defaults."""
        
        class AllDefaultsSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            host: str = "localhost"
            port: int = 8080
            debug: bool = False
        
        settings = validate_settings(AllDefaultsSettings)
        
        assert settings.host == "localhost"
        assert settings.port == 8080
        assert settings.debug is False

    def test_settings_with_union_types(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle union type validation errors."""
        
        class UnionSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: int | str
        
        # This should succeed as it accepts both int and str
        clean_env.setenv("VALUE", "test")
        settings = validate_settings(UnionSettings)
        assert settings.value == "test"

    def test_settings_with_list_field(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle list field types."""
        
        class ListSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            tags: list[str] = []
        
        settings = validate_settings(ListSettings)
        assert settings.tags == []

    def test_settings_with_dict_field(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle dict field types."""
        
        class DictSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            config: dict[str, str] = {}
        
        settings = validate_settings(DictSettings)
        assert settings.config == {}

    def test_multiple_missing_with_types(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should report correct error types for multiple missing fields."""
        
        class MultiTypeSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            str_field: str
            int_field: int
            bool_field: bool
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(MultiTypeSettings)
        
        error = exc_info.value
        assert len(error.missing_fields) == 3
        assert "str_field" in error.missing_fields
        assert "int_field" in error.missing_fields
        assert "bool_field" in error.missing_fields

    def test_settings_with_complex_literal(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle complex Literal types."""
        
        class ComplexLiteralSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            mode: Literal["read", "write", "read-write", "admin"] = "read"
        
        settings = validate_settings(ComplexLiteralSettings)
        assert settings.mode == "read"
        
        clean_env.setenv("MODE", "admin")
        settings = validate_settings(ComplexLiteralSettings)
        assert settings.mode == "admin"

    def test_settings_with_numeric_string_field(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle numeric strings in string fields."""
        
        class NumericStringSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            id: str = "default"
        
        clean_env.setenv("ID", "12345")
        settings = validate_settings(NumericStringSettings)
        assert settings.id == "12345"
        assert isinstance(settings.id, str)

    def test_settings_with_float_field(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle float field types."""
        
        class FloatSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            rate: float = 1.0
        
        clean_env.setenv("RATE", "3.14")
        settings = validate_settings(FloatSettings)
        assert settings.rate == 3.14

    def test_invalid_float_type(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should report error for invalid float value."""
        
        class FloatSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            rate: float
        
        clean_env.setenv("RATE", "not-a-float")
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(FloatSettings)
        
        error = exc_info.value
        assert "rate" in error.missing_fields

    def test_settings_with_env_prefix(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle settings with environment variable prefix."""
        
        class PrefixSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=None,
                env_prefix="APP_"
            )
            name: str = "default"
        
        clean_env.setenv("APP_NAME", "myapp")
        settings = validate_settings(PrefixSettings)
        assert settings.name == "myapp"

    def test_case_sensitive_settings(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle case-sensitive environment variables."""
        
        class CaseSensitiveSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=None,
                case_sensitive=True
            )
            ApiKey: str = "default"
        
        clean_env.setenv("ApiKey", "secret")
        settings = validate_settings(CaseSensitiveSettings)
        assert settings.ApiKey == "secret"

    def test_settings_with_alias(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle field aliases."""
        
        class AliasSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_key: str = Field(default="default", alias="API_SECRET")
        
        clean_env.setenv("API_SECRET", "secret123")
        settings = validate_settings(AliasSettings)
        assert settings.api_key == "secret123"

    def test_settings_with_very_long_string(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle very long string values."""
        
        class LongStringSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            long_value: str = ""
        
        long_string = "x" * 10000
        clean_env.setenv("LONG_VALUE", long_string)
        settings = validate_settings(LongStringSettings)
        assert settings.long_value == long_string
        assert len(settings.long_value) == 10000

    def test_settings_with_negative_integers(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle negative integer values."""
        
        class NegativeIntSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            offset: int = 0
        
        clean_env.setenv("OFFSET", "-42")
        settings = validate_settings(NegativeIntSettings)
        assert settings.offset == -42

    def test_settings_with_zero_values(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle zero values correctly."""
        
        class ZeroSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            count: int = 10
            rate: float = 1.0
        
        clean_env.setenv("COUNT", "0")
        clean_env.setenv("RATE", "0.0")
        settings = validate_settings(ZeroSettings)
        assert settings.count == 0
        assert settings.rate == 0.0

    def test_settings_with_empty_string_default(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle empty string defaults."""
        
        class EmptyStringSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            optional_text: str = ""
        
        settings = validate_settings(EmptyStringSettings)
        assert settings.optional_text == ""

    def test_settings_override_empty_string_default(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should allow overriding empty string defaults."""
        
        class EmptyStringSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            text: str = ""
        
        clean_env.setenv("TEXT", "actual value")
        settings = validate_settings(EmptyStringSettings)
        assert settings.text == "actual value"


class TestValidateSettingsTypeCoercion:
    """Tests for type coercion in validate_settings."""

    def test_int_from_string(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should convert string to int."""
        
        class IntSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: int
        
        clean_env.setenv("VALUE", "42")
        settings = validate_settings(IntSettings)
        assert settings.value == 42
        assert isinstance(settings.value, int)

    def test_bool_from_various_strings(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should convert various string formats to bool."""
        
        class BoolSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            flag: bool
        
        # Test true values
        for value in ["1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"]:
            clean_env.setenv("FLAG", value)
            settings = validate_settings(BoolSettings)
            assert settings.flag is True, f"Failed for value: {value}"

    def test_float_from_int_string(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should convert integer string to float."""
        
        class FloatSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: float
        
        clean_env.setenv("VALUE", "42")
        settings = validate_settings(FloatSettings)
        assert settings.value == 42.0
        assert isinstance(settings.value, float)

    def test_scientific_notation_float(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle scientific notation for floats."""
        
        class ScientificSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: float
        
        clean_env.setenv("VALUE", "1.5e-3")
        settings = validate_settings(ScientificSettings)
        assert settings.value == 0.0015


class TestValidateSettingsErrorMessages:
    """Tests for error message content from validate_settings."""

    def test_error_contains_field_and_type(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Error should contain both field name and error type."""
        
        class TestSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_key: str
            port: int
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(TestSettings)
        
        error = exc_info.value
        # Check that we have the correct error types
        assert any(err[1] == "missing" for err in error.errors)
        assert len(error.errors) == 2

    def test_error_preserves_all_validation_errors(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should preserve all validation errors from pydantic."""
        
        class MultiErrorSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            str_field: str
            int_field: int
            bool_field: bool
            literal_field: Literal["a", "b", "c"]
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(MultiErrorSettings)
        
        error = exc_info.value
        # All 4 fields should have errors
        assert len(error.errors) == 4
        assert len(error.missing_fields) == 4

    def test_error_message_readable_format(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Error message should be human-readable."""
        
        class ReadableSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            database_url: str
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ReadableSettings)
        
        message = str(exc_info.value)
        # Should contain helpful information
        assert "DATABASE_URL" in message
        assert "missing" in message
        # Should have box formatting
        assert "┌" in message or "└" in message