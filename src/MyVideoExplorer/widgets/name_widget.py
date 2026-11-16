from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLineEdit, QWidget

from MyVideoExplorer.tag_cloud.tag_util import validate_name
from MyVideoExplorer.theme.theme import APP_THEME

# Border color shown when a name contains invalid characters.
_NAME_ERROR_BORDER = "#8b3b3b"


class NameWidget(QLineEdit):
    """A QLineEdit that validates its text on blur using the shared name pattern.

    When the user finishes editing (Enter or focus loss), the widget validates
    the name and, if invalid, outlines the text box with a grey-red border and
    sets a tooltip explaining which characters are allowed.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._apply_theme()
        self.editingFinished.connect(self._on_editing_finished)

    def _apply_theme(self) -> None:
        """Apply the current theme font to the line edit."""
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))

    def _on_editing_finished(self) -> None:
        """Validate the current text on blur and update visual feedback."""
        text = self.text().strip()
        is_valid, error_msg = validate_name(text)
        if is_valid:
            self.setToolTip("")
            self._clear_error_border()
        else:
            self.setToolTip(error_msg)
            self._set_error_border()

    def _set_error_border(self) -> None:
        """Outline the text box with an error border."""
        self.setStyleSheet(f"QLineEdit {{ border: 2px solid {_NAME_ERROR_BORDER}; }}")

    def _clear_error_border(self) -> None:
        """Remove the error border styling."""
        self.setStyleSheet("")

    def apply_theme(self) -> None:
        """Re-apply theme styling (called by parent on theme switch)."""
        self._apply_theme()
