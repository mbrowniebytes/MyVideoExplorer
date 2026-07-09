from __future__ import annotations

from MyVideoExplorer.theme.theme import APP_THEME


class ThemableMixin:
    def apply_theme(self) -> None:
        """Default implementation of theme application."""
        if not APP_THEME.is_refreshing:
            APP_THEME.refresh_theme(self)
