from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QWidget

from MyVideoExplorer.theme.theme import APP_THEME


class SelectComboBox(QComboBox):
    """Application-themed combo box for selecting a value from a list."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        APP_THEME.setup_combo_box(self)
