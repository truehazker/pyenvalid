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


class TestConfigurationErrorEdgeCases:
    """Additional edge case tests for ConfigurationError."""

    def test_error_with_whitespace_in_field_name(self) -> None:
        """Should handle field names with whitespace characters."""
        error = ConfigurationError([("field with spaces", "missing")])
        message = str(error)
        
        # Should uppercase and include the field
        assert "FIELD WITH SPACES" in message

    def test_error_with_hyphenated_field_name(self) -> None:
        """Should handle field names with hyphens."""
        error = ConfigurationError([("api-key", "missing")])
        message = str(error)
        
        assert "API-KEY" in message

    def test_error_with_numeric_field_name(self) -> None:
        """Should handle field names that are numeric."""
        error = ConfigurationError([("123field", "missing")])
        message = str(error)
        
        assert "123FIELD" in message

    def test_error_with_all_caps_field_name(self) -> None:
        """Should handle field names already in uppercase."""
        error = ConfigurationError([("API_KEY", "missing")])
        message = str(error)
        
        assert "API_KEY" in message

    def test_error_types_variety(self) -> None:
        """Should handle various pydantic error types."""
        errors = [
            ("field1", "missing"),
            ("field2", "int_parsing"),
            ("field3", "bool_parsing"),
            ("field4", "float_parsing"),
            ("field5", "literal_error"),
            ("field6", "string_type"),
            ("field7", "value_error"),
        ]
        error = ConfigurationError(errors)
        message = str(error)
        
        # All error types should appear
        for field, error_type in errors:
            assert error_type in message

    def test_errors_immutability(self) -> None:
        """Should store errors as a list (not a reference to input)."""
        original_errors = [("field1", "missing")]
        error = ConfigurationError(original_errors)
        
        # Modify original
        original_errors.append(("field2", "missing"))
        
        # Error object should not be affected
        assert len(error.errors) == 1
        assert error.errors[0] == ("field1", "missing")

    def test_empty_title(self) -> None:
        """Should handle empty title string."""
        error = ConfigurationError([("api_key", "missing")], title="")
        message = str(error)
        
        # Should not crash and should still format
        assert "┌" in message
        assert "API_KEY" in message

    def test_empty_hint(self) -> None:
        """Should handle empty hint string."""
        error = ConfigurationError([("api_key", "missing")], hint="")
        message = str(error)
        
        # Should not crash and should still format
        assert "┌" in message
        assert "API_KEY" in message

    def test_newlines_in_title(self) -> None:
        """Should handle newlines in title."""
        error = ConfigurationError(
            [("api_key", "missing")],
            title="CONFIGURATION\nERROR"
        )
        message = str(error)
        
        # Should contain the title (possibly modified)
        assert "CONFIGURATION" in message or "ERROR" in message

    def test_newlines_in_hint(self) -> None:
        """Should handle newlines in hint."""
        error = ConfigurationError(
            [("api_key", "missing")],
            hint="Check your .env file\nOr set environment variables"
        )
        message = str(error)
        
        # Should contain the hint (possibly modified)
        assert "Check your" in message or ".env" in message

    def test_very_many_errors(self) -> None:
        """Should handle a large number of errors."""
        errors = [(f"field_{i}", "missing") for i in range(100)]
        error = ConfigurationError(errors)
        
        assert len(error.errors) == 100
        assert len(error.missing_fields) == 100
        
        message = str(error)
        # Should still format without crashing
        assert "┌" in message

    def test_error_message_contains_environment_text(self) -> None:
        """Should mention environment variables in message."""
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)
        
        assert "environment" in message.lower()

    def test_error_message_line_structure(self) -> None:
        """Should have proper line structure in message."""
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)
        lines = message.split("\n")
        
        # Should have multiple lines
        assert len(lines) > 5
        # First and last should be empty (formatting)
        assert lines[0] == ""
        assert lines[-1] == ""

    def test_error_with_mixed_markers(self) -> None:
        """Should use correct markers for different error types."""
        errors = [
            ("missing_field", "missing"),
            ("invalid_field", "int_parsing"),
            ("another_missing", "missing"),
            ("bad_literal", "literal_error"),
        ]
        error = ConfigurationError(errors)
        message = str(error)
        
        # Count markers
        missing_count = message.count("✗")
        invalid_count = message.count("!")
        
        assert missing_count == 2  # Two "missing" errors
        assert invalid_count == 2  # Two non-"missing" errors

    def test_repr_contains_error_count(self) -> None:
        """Should have a useful repr."""
        error = ConfigurationError([("field1", "missing"), ("field2", "invalid")])
        
        # repr should exist and be informative
        repr_str = repr(error)
        assert "ConfigurationError" in repr_str or "Exception" in repr_str


class TestConfigurationErrorTitle:
    """Tests focused on title formatting."""

    def test_title_with_special_chars(self) -> None:
        """Should handle special characters in title."""
        error = ConfigurationError(
            [("api_key", "missing")],
            title="*** ERROR ***"
        )
        message = str(error)
        
        assert "***" in message

    def test_title_very_short(self) -> None:
        """Should handle very short titles."""
        error = ConfigurationError([("api_key", "missing")], title="X")
        message = str(error)
        
        assert "X" in message

    def test_title_with_digits(self) -> None:
        """Should handle titles with numbers."""
        error = ConfigurationError(
            [("api_key", "missing")],
            title="ERROR 500"
        )
        message = str(error)
        
        assert "500" in message


class TestConfigurationErrorHint:
    """Tests focused on hint formatting."""

    def test_hint_with_urls(self) -> None:
        """Should handle URLs in hints."""
        error = ConfigurationError(
            [("api_key", "missing")],
            hint="See https://docs.example.com for details"
        )
        message = str(error)
        
        assert "https://" in message or "docs.example.com" in message

    def test_hint_with_commands(self) -> None:
        """Should handle command examples in hints."""
        error = ConfigurationError(
            [("api_key", "missing")],
            hint="Run: export API_KEY=your_key"
        )
        message = str(error)
        
        assert "export" in message or "API_KEY" in message

    def test_hint_multiline_content(self) -> None:
        """Should handle multi-line hint content."""
        hint = "Step 1: Create .env file\nStep 2: Add variables\nStep 3: Restart"
        error = ConfigurationError([("api_key", "missing")], hint=hint)
        message = str(error)
        
        # Should contain some hint content
        assert "Step" in message or ".env" in message
