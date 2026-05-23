from __future__ import annotations
import qtawesome as qta
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractButton, QApplication, QComboBox, QLabel, 
    QListWidget, QPlainTextEdit, QTabWidget, QWidget
)
from src.theme.models import ThemeConfig
from src.theme.styles import StyleFactory

class ThemeManager:
    """Orchestrates theme application and widget updates across the application."""
    
    def __init__(self, config: ThemeConfig):
        self.config = config
        self.app: QApplication | None = None
        self._refreshed_app_widgets: set[int] = set()
        self._refreshing: bool = False

    def set_application(self, app: QApplication):
        """Assigns the global application instance for stylesheet management."""
        self.app = app

    def refresh_theme(self, root_widget: QWidget | None = None) -> None:
        """
        Re-applies the theme to the entire application or a specific widget tree.
        Prevents recursion loops using a private state flag.
        """
        if not self.app or self._refreshing:
            return

        self._refreshing = True
        try:
            font = QFont(self.config.font_family_default, self.config.font_size_base)
            
            if root_widget is None:
                # Update global application state
                self.app.setFont(font)
                self.app.setStyleSheet(StyleFactory.get_app_qss(self.config))
                for widget in self.app.topLevelWidgets():
                    self._refresh_recursive(widget, font)
            else:
                self._refresh_recursive(root_widget, font)
        finally:
            self._refreshing = False
            self._refreshed_app_widgets.clear()

    def _refresh_recursive(self, widget: QWidget, font: QFont) -> None:
        if not widget:
            return

        # Handle Custom Application Widgets (prefixed with src.)
        if self._is_custom_widget(widget):
            if id(widget) in self._refreshed_app_widgets:
                return
            self._refreshed_app_widgets.add(id(widget))
            if hasattr(widget, "apply_theme"):
                widget.apply_theme()
            return

        # Handle Standard Qt Widgets
        if isinstance(widget, (QLabel, QPlainTextEdit, QListWidget, QTabWidget, QAbstractButton)):
            widget.setFont(font)
            if isinstance(widget, QPlainTextEdit):
                widget.document().setDefaultFont(font)

    def _is_custom_widget(self, widget: QWidget) -> bool:
        """Checks if the widget belongs to our internal source code namespace."""
        module_name = getattr(widget.__class__, "__module__", "")
        return module_name.startswith("src.")

    def get_icon(self, name: str, **kwargs) -> QIcon:
        """Safely fetch icons with a fallback to a folder icon if the name is missing."""
        try:
            return qta.icon(name, **kwargs)
        except Exception:
            try:
                return qta.icon("fa5s.folder", **kwargs)
            except Exception:
                return QIcon()

    # Focused Widget Setup Helpers
    def setup_list_widget(self, widget: QListWidget) -> None:
        widget.setStyleSheet(StyleFactory.get_list_qss(self.config))
        widget.setAlternatingRowColors(True)
        from PySide6.QtCore import QSize
        widget.setIconSize(QSize(self.config.size_standard_icon, self.config.size_standard_icon))

    def setup_combo_box(self, widget: QComboBox) -> None:
        widget.setStyleSheet(StyleFactory.get_combo_qss(self.config))

    def setup_button(self, widget: QAbstractButton) -> None:
        widget.setStyleSheet(StyleFactory.get_button_qss(self.config))
        if hasattr(widget, "setMinimumHeight"):
            widget.setMinimumHeight(self.config.size_button_minimum_height)