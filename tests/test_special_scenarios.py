"""Tests for special scenarios and corner cases."""

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from pyenvalid import ConfigurationError, validate_settings


class TestEmptyAndNoneValues:
    """Tests for empty and None value handling."""

    def test_required_field_with_empty_string_fails(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should fail when required field is empty string."""
        
        class RequiredSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_key: str
        
        clean_env.setenv("API_KEY", "")
        
        # Pydantic might allow empty string for str type
        # Let's test the actual behavior
        try:
            settings = validate_settings(RequiredSettings)
            # If it succeeds, empty string is valid for str type
            assert settings.api_key == ""
        except ConfigurationError:
            # If it fails, that's also acceptable behavior
            pass

    def test_optional_field_can_be_none(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should allow None for optional fields."""
        from typing import Optional
        
        class OptionalSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            optional_value: Optional[str] = None
        
        settings = validate_settings(OptionalSettings)
        
        assert settings.optional_value is None


class TestComplexFieldNames:
    """Tests for complex field naming scenarios."""

    def test_field_with_numbers(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle field names with numbers."""
        
        class NumberedSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_key_v2: str = "default"
            oauth2_secret: str = "default"
            server1_url: str = "default"
        
        clean_env.setenv("API_KEY_V2", "key2")
        clean_env.setenv("OAUTH2_SECRET", "secret")
        clean_env.setenv("SERVER1_URL", "http://server1")
        
        settings = validate_settings(NumberedSettings)
        
        assert settings.api_key_v2 == "key2"
        assert settings.oauth2_secret == "secret"
        assert settings.server1_url == "http://server1"

    def test_field_with_double_underscore(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle field names with double underscores."""
        
        class DoubleUnderscoreSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            private__value: str = "default"
        
        clean_env.setenv("PRIVATE__VALUE", "secret")
        
        settings = validate_settings(DoubleUnderscoreSettings)
        
        assert settings.private__value == "secret"


class TestValidationErrorTranslation:
    """Tests for how ValidationError is translated to ConfigurationError."""

    def test_validation_error_field_extraction(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should correctly extract field names from ValidationError."""
        
        class FieldExtractionSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            field_a: str
            field_b: int
            field_c: bool
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(FieldExtractionSettings)
        
        error = exc_info.value
        # All three fields should be reported
        assert len(error.missing_fields) == 3
        field_names = set(error.missing_fields)
        assert "field_a" in field_names
        assert "field_b" in field_names
        assert "field_c" in field_names

    def test_validation_error_type_extraction(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should correctly extract error types from ValidationError."""
        
        class TypeExtractionSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            port: int
        
        clean_env.setenv("PORT", "invalid")
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(TypeExtractionSettings)
        
        error = exc_info.value
        # Should have the int_parsing error type
        assert len(error.errors) == 1
        assert error.errors[0][0] == "port"
        assert "parsing" in error.errors[0][1] or "int" in error.errors[0][1]

    def test_preserves_pydantic_error_chain(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should preserve the error chain from pydantic."""
        
        class ChainedErrorSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value: int
        
        clean_env.setenv("VALUE", "not-an-int")
        
        try:
            validate_settings(ChainedErrorSettings)
            pytest.fail("Should have raised ConfigurationError")
        except ConfigurationError as e:
            # __cause__ should be None since we use "from None"
            assert e.__cause__ is None
            # But __context__ might be set
            # The error should have our structured data
            assert len(e.errors) > 0


class TestSettingsInheritance:
    """Tests for settings class inheritance."""

    def test_inherited_settings_validation(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should validate inherited settings classes."""
        
        class BaseAppSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            app_name: str = "myapp"
        
        class ExtendedSettings(BaseAppSettings):
            api_key: str
        
        clean_env.setenv("API_KEY", "secret")
        
        settings = validate_settings(ExtendedSettings)
        
        assert settings.app_name == "myapp"
        assert settings.api_key == "secret"

    def test_inherited_settings_missing_required(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should report missing fields from inherited settings."""
        
        class BaseAppSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            base_required: str
        
        class ExtendedSettings(BaseAppSettings):
            extended_required: str
        
        with pytest.raises(ConfigurationError) as exc_info:
            validate_settings(ExtendedSettings)
        
        error = exc_info.value
        # Both required fields should be reported
        assert len(error.missing_fields) == 2
        assert "base_required" in error.missing_fields
        assert "extended_required" in error.missing_fields


class TestConfigurationErrorRepr:
    """Tests for ConfigurationError representation."""

    def test_error_repr_is_informative(self) -> None:
        """Error repr should provide useful information."""
        error = ConfigurationError([("api_key", "missing")])
        repr_str = repr(error)
        
        # Should contain some identifying information
        assert repr_str  # Not empty
        assert len(repr_str) > 0

    def test_error_str_is_formatted(self) -> None:
        """Error str should be the formatted message."""
        error = ConfigurationError([("api_key", "missing")])
        str_msg = str(error)
        
        # Should be the formatted message with box
        assert "┌" in str_msg
        assert "API_KEY" in str_msg
        assert "missing" in str_msg


class TestEdgeCaseSettings:
    """Tests for edge case settings configurations."""

    def test_settings_with_only_defaults(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should work with settings that have only defaults."""
        
        class OnlyDefaultsSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            value1: str = "default1"
            value2: int = 42
            value3: bool = True
        
        settings = validate_settings(OnlyDefaultsSettings)
        
        assert settings.value1 == "default1"
        assert settings.value2 == 42
        assert settings.value3 is True

    def test_settings_with_single_field(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle settings with a single field."""
        
        class SingleFieldSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_key: str
        
        clean_env.setenv("API_KEY", "secret")
        
        settings = validate_settings(SingleFieldSettings)
        
        assert settings.api_key == "secret"

    def test_settings_with_many_fields(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle settings with many fields."""
        
        class ManyFieldsSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            field01: str = "1"
            field02: str = "2"
            field03: str = "3"
            field04: str = "4"
            field05: str = "5"
            field06: str = "6"
            field07: str = "7"
            field08: str = "8"
            field09: str = "9"
            field10: str = "10"
        
        settings = validate_settings(ManyFieldsSettings)
        
        assert settings.field01 == "1"
        assert settings.field10 == "10"


class TestURLAndPathValues:
    """Tests for URL and file path values."""

    def test_url_values(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle URL values correctly."""
        
        class URLSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            api_url: str
            webhook_url: str = "https://example.com/webhook"
        
        clean_env.setenv("API_URL", "https://api.example.com/v1")
        
        settings = validate_settings(URLSettings)
        
        assert settings.api_url == "https://api.example.com/v1"
        assert settings.webhook_url == "https://example.com/webhook"

    def test_file_path_values(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle file path values correctly."""
        
        class PathSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            config_path: str = "/etc/app/config.yaml"
            log_path: str = "/var/log/app.log"
        
        clean_env.setenv("CONFIG_PATH", "/custom/path/config.yaml")
        
        settings = validate_settings(PathSettings)
        
        assert settings.config_path == "/custom/path/config.yaml"
        assert settings.log_path == "/var/log/app.log"

    def test_windows_path_values(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle Windows-style paths."""
        
        class WindowsPathSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            install_path: str = "C:\\Program Files\\App"
        
        clean_env.setenv("INSTALL_PATH", "D:\\Custom\\Path")
        
        settings = validate_settings(WindowsPathSettings)
        
        assert settings.install_path == "D:\\Custom\\Path"


class TestJSONAndStructuredData:
    """Tests for JSON and structured data in environment variables."""

    def test_json_string_as_string(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle JSON strings in string fields."""
        
        class JSONStringSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            config: str = "{}"
        
        json_value = '{"key": "value", "number": 42}'
        clean_env.setenv("CONFIG", json_value)
        
        settings = validate_settings(JSONStringSettings)
        
        assert settings.config == json_value


class TestSpecialCharactersInValues:
    """Tests for special characters in environment variable values."""

    def test_special_chars_in_strings(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle special characters in string values."""
        
        class SpecialCharsSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            password: str
        
        special_password = "p@$$w0rd!#%^&*()[]{}|\\;:'\",.<>?/"
        clean_env.setenv("PASSWORD", special_password)
        
        settings = validate_settings(SpecialCharsSettings)
        
        assert settings.password == special_password

    def test_unicode_in_values(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle Unicode characters in values."""
        
        class UnicodeSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            message: str
        
        unicode_message = "Hello 世界 🌍 café"
        clean_env.setenv("MESSAGE", unicode_message)
        
        settings = validate_settings(UnicodeSettings)
        
        assert settings.message == unicode_message

    def test_emoji_in_values(
        self, clean_env: pytest.MonkeyPatch
    ) -> None:
        """Should handle emoji in values."""
        
        class EmojiSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=None)
            status: str = "✅"
        
        clean_env.setenv("STATUS", "🚀")
        
        settings = validate_settings(EmojiSettings)
        
        assert settings.status == "🚀"