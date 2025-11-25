"""Tests for ConfigurationError exception."""

import pytest

from pyenvalid import ConfigurationError


class TestConfigurationError:
    """Tests for ConfigurationError class."""

    def test_stores_errors(self) -> None:
        """Should store errors as list of tuples."""
        errors = [("api_key", "missing"), ("port", "int_parsing")]
        error = ConfigurationError(errors)

        assert error.errors == errors

    def test_missing_fields_backwards_compatibility(self) -> None:
        """Should expose missing_fields for backwards compatibility."""
        errors = [("field1", "missing"), ("field2", "invalid")]
        error = ConfigurationError(errors)

        assert error.missing_fields == ["field1", "field2"]

    def test_message_contains_title(self) -> None:
        """Error message should contain the title."""
        error = ConfigurationError([("api_key", "missing")])

        assert "CONFIGURATION ERROR" in str(error)

    def test_custom_title(self) -> None:
        """Should support custom title."""
        error = ConfigurationError([("api_key", "missing")], title="STARTUP FAILED")

        assert "STARTUP FAILED" in str(error)

    def test_message_contains_hint(self) -> None:
        """Error message should contain the hint."""
        error = ConfigurationError([("api_key", "missing")])

        assert "Set these in your .env file or environment" in str(error)

    def test_custom_hint(self) -> None:
        """Should support custom hint."""
        error = ConfigurationError(
            [("api_key", "missing")], hint="Check your config file"
        )

        assert "Check your config file" in str(error)

    def test_message_contains_field_names(self) -> None:
        """Error message should list all field names in uppercase."""
        errors = [("database_url", "missing"), ("api_key", "invalid")]
        error = ConfigurationError(errors)
        message = str(error)

        assert "DATABASE_URL" in message
        assert "API_KEY" in message

    def test_message_contains_error_types(self) -> None:
        """Error message should show error types."""
        errors = [("api_key", "missing"), ("port", "int_parsing")]
        error = ConfigurationError(errors)
        message = str(error)

        assert "missing" in message
        assert "int_parsing" in message

    def test_empty_errors_handled_gracefully(self) -> None:
        """Should handle empty errors list without crashing."""
        error = ConfigurationError([])

        assert "No errors" in str(error)
        assert error.missing_fields == []

    def test_single_field_error(self) -> None:
        """Should work with single field error."""
        error = ConfigurationError([("api_key", "missing")])

        assert len(error.missing_fields) == 1
        assert "API_KEY" in str(error)

    def test_many_fields_error(self) -> None:
        """Should handle many field errors."""
        errors = [(f"field_{i}", "missing") for i in range(10)]
        error = ConfigurationError(errors)

        assert len(error.missing_fields) == 10

    def test_message_has_box_structure(self) -> None:
        """Error message should have box drawing characters."""
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)

        # Check for box drawing characters
        assert "┌" in message
        assert "┐" in message
        assert "└" in message
        assert "┘" in message
        assert "│" in message
        assert "─" in message

    def test_missing_marker_for_missing_fields(self) -> None:
        """Should use ✗ marker for missing fields."""
        error = ConfigurationError([("api_key", "missing")])

        assert "✗" in str(error)

    def test_exclamation_marker_for_invalid_fields(self) -> None:
        """Should use ! marker for invalid fields."""
        error = ConfigurationError([("port", "int_parsing")])

        assert "!" in str(error)


class TestConfigurationErrorInheritance:
    """Tests for ConfigurationError inheritance."""

    def test_is_exception(self) -> None:
        """Should be an Exception subclass."""
        error = ConfigurationError([("api_key", "missing")])
        assert isinstance(error, Exception)

    def test_can_be_raised(self) -> None:
        """Should be raisable."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError([("api_key", "missing")])

    def test_can_be_caught_as_exception(self) -> None:
        """Should be catchable as Exception."""
        try:
            raise ConfigurationError([("api_key", "missing")])
        except Exception as e:
            assert isinstance(e, ConfigurationError)
