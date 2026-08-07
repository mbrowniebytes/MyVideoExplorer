from __future__ import annotations

from PySide6.QtWidgets import QWidget

from MyVideoExplorer.theme.theme import APP_THEME


class ThemableMixin:
    def apply_theme(self: QWidget) -> None:
        """Default implementation of theme application."""
        if not APP_THEME.is_refreshing:
            APP_THEME.refresh_theme(self)
