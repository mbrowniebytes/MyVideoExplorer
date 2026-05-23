from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLayout, QVBoxLayout
from src.theme.theme import APP_THEME


class BaseWidget(QWidget):
    """Base class for all widgets in the application to reduce boilerplate."""

    def __init__(self, log_util=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def set_compact_layout(self, layout_type: type[QLayout] = QVBoxLayout) -> QLayout:
        """Creates and sets a layout with 0 margins and 0 spacing."""
        layout = layout_type(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        return layout

    def apply_theme(self) -> None:
        """Default implementation of theme application."""
        self.setStyleSheet(APP_THEME.container_qss())

    @staticmethod
    def clear_layout(layout: QLayout | None) -> None:
        """Utility to safely clear all widgets and sub-layouts from a layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                BaseWidget.clear_layout(item.layout())
