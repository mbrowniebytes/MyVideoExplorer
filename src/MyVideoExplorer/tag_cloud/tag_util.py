from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QToolButton


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
        " border: 1px solid palette(mid); border-radius: 3px; padding: 2px;"
        "}"
    )


def validate_tag_name(name: str) -> tuple[bool, str]:
    """Validate a tag name to ensure non-empty and alphanumeric characters."""
    cleaned = name.strip()
    if not cleaned:
        return False, "Tag name cannot be empty."
    if not cleaned.isalnum():
        return False, "Tag names must be alphanumeric only."
    return True, ""
