from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QToolButton, QWidget

from MyVideoExplorer.theme.models import ThemeConfig
from MyVideoExplorer.theme.theme import APP_THEME


class ActionButton(QToolButton):
    """Reusable icon-forward button for compact UI actions."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        icon_name: str | None = None,
        tooltip: str | None = None,
        icon_color: str | None = None,
        icon_size: int | QSize | None = None,
        text: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("action_button", True)
        if text is not None:
            self.setText(text)
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        if text or tooltip:
            self.setAccessibleName(text or tooltip or "")
        self.setAutoRaise(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon_size is None:
            icon_size = APP_THEME.icon_size
        if isinstance(icon_size, int):
            icon_size = QSize(icon_size, icon_size)
        self.setIconSize(icon_size)
        if icon_name is not None:
            self.set_action_icon(icon_name, color=icon_color)
        if tooltip is not None:
            self.setToolTip(tooltip)
        self.setStyleSheet(self.action_style_sheet())

    @staticmethod
    def action_style_sheet(config: ThemeConfig | None = None) -> str:
        config = config or APP_THEME.config
        return f"""
            QToolButton {{
                color: {config.color_text_primary};
                background: {config.color_surface_primary};
                border: 1px solid {config.color_surface_primary};
                border-radius: {config.size_border_radius_standard}px;
                padding: 2px;
            }}
            QToolButton:hover {{
                background: {config.color_interaction_hover};
                border-color: {config.color_interaction_hover};
            }}
            QToolButton:pressed {{
                background: {config.color_interaction_pressed};
                border-color: {config.color_interaction_pressed};
            }}
            QToolButton:disabled {{
                background: {config.color_surface_disabled};
                border-color: {config.color_surface_disabled};
            }}
        """

    def set_action_icon(self, icon_name: str, *, color: str | None = None) -> None:
        self.setIcon(APP_THEME.icon(icon_name, color=color or APP_THEME.text_color))
