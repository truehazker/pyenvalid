"""Validation utilities for pydantic-settings."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, TypeVar

from pydantic import ValidationError
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from collections.abc import Sequence

T = TypeVar("T", bound=BaseSettings)


class ConfigurationError(Exception):
    """Raised when settings validation fails due to missing or invalid fields."""

    def __init__(
        self,
        errors: Sequence[tuple[str, str]],
        *,
        title: str = "CONFIGURATION ERROR",
        hint: str = "Set these in your .env file or environment",
    ) -> None:
        """Initialize ConfigurationError with validation errors.

        Args:
            errors: Sequence of (field_name, error_type) tuples.
            title: Title for the error box.
            hint: Hint message shown at the bottom.
        """
        self.errors = list(errors)
        self.title = title
        self.hint = hint
        # For backwards compatibility
        self.missing_fields = [field for field, _ in self.errors]
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format a beautiful error message with dynamic width."""
        if not self.errors:
            return f"\n{self.title}: No errors\n"

        term_width = self._get_terminal_width()
        box = _BoxFormatter(term_width)

        lines = [
            "",
            box.top(),
            box.line(self.title),
            box.separator(),
            box.line(),
            box.line("The following environment variables have issues:"),
            box.line(),
        ]

        for field, error_type in self.errors:
            marker = "✗" if error_type == "missing" else "!"
            lines.append(box.line(f"  {marker} {field.upper()} ({error_type})"))

        lines.extend(
            [
                box.line(),
                box.separator(),
                box.line(self.hint),
                box.bottom(),
                "",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _get_terminal_width() -> int:
        """Get terminal width with fallback."""
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 80


class _BoxFormatter:
    """Helper class for formatting box-style messages."""

    def __init__(
        self, term_width: int, *, min_width: int = 30, max_width: int = 80
    ) -> None:
        # Clamp box width: at least min_width, at most max_width or terminal width
        self.box_width = max(min_width, min(max_width, term_width - 4))
        self.inner_width = self.box_width - 4

    def _truncate(self, text: str) -> str:
        """Truncate text if it exceeds inner width."""
        if len(text) <= self.inner_width:
            return text
        return text[: self.inner_width - 3] + "..."

    def line(self, text: str = "") -> str:
        """Create a padded line with truncation."""
        truncated = self._truncate(text)
        padding = self.inner_width - len(truncated)
        return f"│ {truncated}{' ' * padding} │"

    def top(self) -> str:
        """Create the top border."""
        return "┌" + "─" * (self.box_width - 2) + "┐"

    def bottom(self) -> str:
        """Create the bottom border."""
        return "└" + "─" * (self.box_width - 2) + "┘"

    def separator(self) -> str:
        """Create a horizontal separator."""
        return "├" + "─" * (self.box_width - 2) + "┤"


def validate_settings(settings_class: type[T]) -> T:
    """Validate and instantiate a pydantic-settings class.

    This function attempts to create an instance of the given settings class,
    which will load values from environment variables (and .env files if configured).
    If validation fails, it raises a ConfigurationError with a formatted message.

    Args:
        settings_class: A pydantic-settings BaseSettings subclass to validate.

    Returns:
        An instance of the validated settings class.

    Raises:
        ConfigurationError: If validation fails due to missing or invalid fields.

    Example:
        >>> from pydantic_settings import BaseSettings
        >>> class MySettings(BaseSettings):
        ...     api_key: str
        ...     port: int = 8080
        >>> settings = validate_settings(MySettings)  # Raises if API_KEY not set
    """
    try:
        return settings_class()
    except ValidationError as e:
        errors: list[tuple[str, str]] = []
        for err in e.errors():
            field = str(err["loc"][0]) if err["loc"] else "unknown"
            errors.append((field, err["type"]))
        raise ConfigurationError(errors) from None
