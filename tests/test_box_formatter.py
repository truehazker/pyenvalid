"""Tests for _BoxFormatter class and message formatting edge cases."""

import pytest

from pyenvalid.validation import ConfigurationError, _BoxFormatter


class TestBoxFormatter:
    """Tests for the _BoxFormatter helper class."""

    def test_default_initialization(self) -> None:
        """Should initialize with default min and max widths."""
        formatter = _BoxFormatter(100)
        
        # Terminal width 100, minus 4 = 96, but clamped to max_width 80
        assert formatter.box_width == 80
        assert formatter.inner_width == 76

    def test_small_terminal_width(self) -> None:
        """Should use min_width when terminal is too narrow."""
        formatter = _BoxFormatter(20)
        
        # 20 - 4 = 16, but min_width is 30
        assert formatter.box_width == 30
        assert formatter.inner_width == 26

    def test_medium_terminal_width(self) -> None:
        """Should use terminal width when between min and max."""
        formatter = _BoxFormatter(50)
        
        # 50 - 4 = 46, which is between 30 and 80
        assert formatter.box_width == 46
        assert formatter.inner_width == 42

    def test_large_terminal_width(self) -> None:
        """Should clamp to max_width for large terminals."""
        formatter = _BoxFormatter(200)
        
        # 200 - 4 = 196, but clamped to max_width 80
        assert formatter.box_width == 80
        assert formatter.inner_width == 76

    def test_custom_min_width(self) -> None:
        """Should respect custom min_width parameter."""
        formatter = _BoxFormatter(10, min_width=50)
        
        assert formatter.box_width == 50
        assert formatter.inner_width == 46

    def test_custom_max_width(self) -> None:
        """Should respect custom max_width parameter."""
        formatter = _BoxFormatter(200, max_width=100)
        
        assert formatter.box_width == 100
        assert formatter.inner_width == 96

    def test_custom_min_and_max_width(self) -> None:
        """Should respect both custom min and max widths."""
        formatter = _BoxFormatter(80, min_width=40, max_width=60)
        
        # 80 - 4 = 76, clamped to max_width 60
        assert formatter.box_width == 60
        assert formatter.inner_width == 56

    def test_truncate_short_text(self) -> None:
        """Should not truncate text shorter than inner width."""
        formatter = _BoxFormatter(100)
        text = "Short text"
        
        result = formatter._truncate(text)
        
        assert result == text
        assert "..." not in result

    def test_truncate_exact_length(self) -> None:
        """Should not truncate text exactly at inner width."""
        formatter = _BoxFormatter(100)
        text = "x" * formatter.inner_width
        
        result = formatter._truncate(text)
        
        assert result == text
        assert "..." not in result

    def test_truncate_long_text(self) -> None:
        """Should truncate text longer than inner width."""
        formatter = _BoxFormatter(100)
        text = "x" * (formatter.inner_width + 10)
        
        result = formatter._truncate(text)
        
        assert len(result) == formatter.inner_width
        assert result.endswith("...")
        assert result == "x" * (formatter.inner_width - 3) + "..."

    def test_truncate_very_long_text(self) -> None:
        """Should handle very long text truncation."""
        formatter = _BoxFormatter(100)
        text = "x" * 1000
        
        result = formatter._truncate(text)
        
        assert len(result) == formatter.inner_width
        assert result.endswith("...")

    def test_line_empty_text(self) -> None:
        """Should create properly padded empty line."""
        formatter = _BoxFormatter(50)
        
        result = formatter.line()
        
        assert result.startswith("│ ")
        assert result.endswith(" │")
        assert len(result) == formatter.box_width

    def test_line_with_text(self) -> None:
        """Should create properly padded line with text."""
        formatter = _BoxFormatter(50)
        text = "Test message"
        
        result = formatter.line(text)
        
        assert result.startswith("│ Test message")
        assert result.endswith(" │")
        assert len(result) == formatter.box_width
        assert text in result

    def test_line_truncates_long_text(self) -> None:
        """Should truncate text in line when too long."""
        formatter = _BoxFormatter(50)
        text = "x" * 100
        
        result = formatter.line(text)
        
        assert "..." in result
        assert len(result) == formatter.box_width

    def test_line_padding_calculation(self) -> None:
        """Should calculate padding correctly for various text lengths."""
        formatter = _BoxFormatter(50)
        
        short_line = formatter.line("Hi")
        medium_line = formatter.line("Hello World")
        
        # All lines should have same total length
        assert len(short_line) == len(medium_line) == formatter.box_width

    def test_top_border(self) -> None:
        """Should create correct top border."""
        formatter = _BoxFormatter(50)
        
        result = formatter.top()
        
        assert result.startswith("┌")
        assert result.endswith("┐")
        assert len(result) == formatter.box_width
        assert result.count("─") == formatter.box_width - 2

    def test_bottom_border(self) -> None:
        """Should create correct bottom border."""
        formatter = _BoxFormatter(50)
        
        result = formatter.bottom()
        
        assert result.startswith("└")
        assert result.endswith("┘")
        assert len(result) == formatter.box_width
        assert result.count("─") == formatter.box_width - 2

    def test_separator(self) -> None:
        """Should create correct separator line."""
        formatter = _BoxFormatter(50)
        
        result = formatter.separator()
        
        assert result.startswith("├")
        assert result.endswith("┤")
        assert len(result) == formatter.box_width
        assert result.count("─") == formatter.box_width - 2

    def test_consistent_width_across_elements(self) -> None:
        """Should maintain consistent width across all box elements."""
        formatter = _BoxFormatter(60)
        
        top = formatter.top()
        line = formatter.line("Test")
        sep = formatter.separator()
        bottom = formatter.bottom()
        
        assert len(top) == len(line) == len(sep) == len(bottom)


class TestConfigurationErrorMessageFormatting:
    """Tests for edge cases in ConfigurationError message formatting."""

    def test_very_long_field_name(self) -> None:
        """Should handle very long field names."""
        long_field = "very_long_configuration_field_name_that_exceeds_normal_length"
        error = ConfigurationError([(long_field, "missing")])
        message = str(error)
        
        # Should contain uppercase version (possibly truncated)
        assert "VERY_LONG" in message

    def test_field_name_with_special_characters(self) -> None:
        """Should handle field names with underscores and numbers."""
        error = ConfigurationError([("api_key_v2", "missing"), ("db_url_1", "missing")])
        message = str(error)
        
        assert "API_KEY_V2" in message
        assert "DB_URL_1" in message

    def test_unicode_in_custom_title(self) -> None:
        """Should handle unicode characters in custom title."""
        error = ConfigurationError(
            [("api_key", "missing")],
            title="⚠️ CONFIGURATION ERROR ⚠️"
        )
        message = str(error)
        
        assert "⚠️" in message

    def test_unicode_in_custom_hint(self) -> None:
        """Should handle unicode characters in custom hint."""
        error = ConfigurationError(
            [("api_key", "missing")],
            hint="💡 Check your .env file"
        )
        message = str(error)
        
        assert "💡" in message

    def test_very_long_custom_title(self) -> None:
        """Should handle very long custom titles."""
        long_title = "CRITICAL CONFIGURATION ERROR " * 10
        error = ConfigurationError([("api_key", "missing")], title=long_title)
        message = str(error)
        
        # Should contain at least part of the title
        assert "CRITICAL" in message

    def test_very_long_custom_hint(self) -> None:
        """Should handle very long custom hints."""
        long_hint = "Please check your environment configuration " * 10
        error = ConfigurationError([("api_key", "missing")], hint=long_hint)
        message = str(error)
        
        # Should contain at least part of the hint
        assert "Please check" in message or "..." in message

    def test_empty_field_name(self) -> None:
        """Should handle empty field name gracefully."""
        error = ConfigurationError([("", "missing")])
        message = str(error)
        
        # Should not crash
        assert "missing" in message

    def test_multiple_errors_same_field(self) -> None:
        """Should handle multiple error types for same field."""
        # This tests the data structure, though pydantic typically reports one error per field
        error = ConfigurationError([
            ("api_key", "missing"),
            ("api_key", "string_type")
        ])
        
        assert len(error.errors) == 2
        assert error.errors[0] == ("api_key", "missing")
        assert error.errors[1] == ("api_key", "string_type")

    def test_errors_order_preserved(self) -> None:
        """Should preserve the order of errors."""
        errors = [
            ("field_z", "missing"),
            ("field_a", "invalid"),
            ("field_m", "type_error")
        ]
        error = ConfigurationError(errors)
        
        assert error.errors == errors
        assert error.missing_fields == ["field_z", "field_a", "field_m"]

    def test_mixed_error_types(self) -> None:
        """Should display both missing and invalid error markers."""
        error = ConfigurationError([
            ("field1", "missing"),
            ("field2", "int_parsing"),
            ("field3", "missing"),
            ("field4", "literal_error")
        ])
        message = str(error)
        
        # Should have both markers
        assert "✗" in message  # missing marker
        assert "!" in message  # invalid marker

    def test_message_structure_completeness(self) -> None:
        """Should have complete message structure."""
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)
        
        # Should have all structural elements
        assert message.startswith("\n")
        assert message.endswith("\n")
        assert "┌" in message
        assert "└" in message
        assert "├" in message
        assert "│" in message


class TestTerminalWidthHandling:
    """Tests for terminal width detection and fallback."""

    def test_get_terminal_width_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should fallback to 80 when terminal size cannot be determined."""
        import shutil
        
        def mock_get_terminal_size() -> None:
            raise OSError("No terminal")
        
        monkeypatch.setattr(shutil, "get_terminal_size", mock_get_terminal_size)
        
        width = ConfigurationError._get_terminal_width()
        
        assert width == 80

    def test_message_formatting_with_fallback_width(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should format message correctly with fallback width."""
        import shutil
        
        def mock_get_terminal_size() -> None:
            raise ValueError("Terminal error")
        
        monkeypatch.setattr(shutil, "get_terminal_size", mock_get_terminal_size)
        
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)
        
        # Should still format correctly
        assert "┌" in message
        assert "API_KEY" in message

    def test_message_formatting_narrow_terminal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should format message correctly in narrow terminal."""
        import shutil
        from collections import namedtuple
        
        TerminalSize = namedtuple("TerminalSize", ["columns", "lines"])
        monkeypatch.setattr(
            shutil, "get_terminal_size", lambda: TerminalSize(40, 24)
        )
        
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)
        
        # Should still format correctly with minimum width
        assert "┌" in message
        assert "API_KEY" in message

    def test_message_formatting_wide_terminal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should format message correctly in wide terminal."""
        import shutil
        from collections import namedtuple
        
        TerminalSize = namedtuple("TerminalSize", ["columns", "lines"])
        monkeypatch.setattr(
            shutil, "get_terminal_size", lambda: TerminalSize(200, 50)
        )
        
        error = ConfigurationError([("api_key", "missing")])
        message = str(error)
        
        # Should clamp to max width
        assert "┌" in message
        assert "API_KEY" in message