from __future__ import annotations

import re

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QToolButton

# Shared name validation pattern for tags, filters, and media folder names.
# Allows alphanumeric characters, spaces, and common ASCII punctuation, excluding
# slashes, backslashes, quotes, and control characters for JSON safety.
VALID_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 _|!@#$%^&{}\[\](),.:+~*=\-]+$")


def validate_name(name: str) -> tuple[bool, str]:
    """Validate a name for tags, filters, or media folder labels.

    Args:
        name: The name to validate.

    Returns:
        A tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    cleaned = name.strip()
    if not cleaned:
        return False, "Name cannot be empty."
    if not VALID_NAME_PATTERN.fullmatch(cleaned):
        return (
            False,
            (
                "Name may only contain letters, numbers, spaces,\nand the symbols: "
                "- _ | ! @ # $ % ^ & { } [ ] ( ) , . : + ~ * ="
            ),
        )
    return True, ""


def get_contrast_text_color(color: str) -> str:
    """Return #000000 or #ffffff depending on background luminance for high contrast."""
    background = QColor(color)
    if not background.isValid():
        return "#000000"
    luminance = (
        0.299 * background.red()
        + 0.587 * background.green()
        + 0.114 * background.blue()
    )
    return "#000000" if luminance > 150 else "#ffffff"


def style_painter_button(button: QToolButton, color: str) -> None:
    """Style a palette tool button with background color and standard border."""
    button.setProperty("preserve_custom_style", True)
    button.setStyleSheet(
        "QToolButton {"
        f" background-color: {color};"
        f" border: 1px solid {color}; border-radius: 3px; padding: 2px;"
        "}"
    )


def validate_tag_name(name: str) -> tuple[bool, str]:
    """Validate a tag name using the shared name validation pattern."""
    return validate_name(name)
