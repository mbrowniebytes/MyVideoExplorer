from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QToolButton, QSizePolicy

from src.theme.theme import APP_THEME


class NavButton(QToolButton):
    """
    Standard navigation button for FolderNav.
    """

    def __init__(self, label: str, icon_name: str = "folder", parent=None):
        super().__init__(parent)
        self._setup_ui(label, icon_name)

    def _setup_ui(self, label: str, icon_name: str) -> None:
        self.setToolTip(label)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Map some common theme icons to qtawesome if they are used as defaults
        if icon_name == "folder":
            icon_name = "fa5s.folder"

        self.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        self.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(70, 40)

        self.setText(label)
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
