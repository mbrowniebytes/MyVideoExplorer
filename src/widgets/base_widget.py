
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QLayout, QVBoxLayout
from src.theme.theme import APP_THEME
from src.utils.log_util import LogUtil


class BaseWidget(QWidget):
    """Base class for all widgets in the application to reduce boilerplate."""

    def __init__(self, log_util: LogUtil | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def set_compact_layout(self, layout_type: type[QLayout] = QVBoxLayout) -> QLayout:
        """Creates and sets a layout with 0 margins and 0 spacing."""
        if self.layout() is not None:
            raise RuntimeError("Widget already has a layout. Clear it first or use clear_self_layout().")

        layout = layout_type(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
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

    def clear_self_layout(self) -> None:
        """Convenience method to clear the widget's own layout."""
        self.clear_layout(self.layout())
