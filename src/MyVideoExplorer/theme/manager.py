from __future__ import annotations

from typing import Any

import qtawesome as qta  # type: ignore[import-untyped]
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabBar,
    QTabWidget,
    QToolButton,
    QWidget,
)

from MyVideoExplorer.theme.theme import StyleFactory, ThemeConfig


class ThemeManager:
    """Orchestrates theme application and widget updates across the application."""

    def __init__(self, config: ThemeConfig):
        self.config = config
        self.app: QApplication | None = None
        self._refreshed_widgets: set[int] = set()
        self._refreshing: bool = False

    @property
    def is_refreshing(self) -> bool:
        """Indicates if a theme refresh is currently in progress."""
        return self._refreshing

    def set_application(self, app: QApplication) -> None:
        """Assigns the global application instance for stylesheet management."""
        self.app = app

    def refresh_theme(self, root_widget: QWidget | None = None) -> None:
        """
        Re-applies the theme to the entire application or a specific widget tree.
        Prevents recursion loops using a private state flag.
        """
        if not self.app and root_widget is None:
            return

        if self._refreshing:
            return

        self._refreshing = True
        self._refreshed_widgets.clear()
        try:
            # Using pixelSize ensures consistent sizing across widgets and QSS,
            # avoiding ambiguity between pointSize and pixelSize in different environments.
            font = QFont(self.config.font_family_default)
            font.setPixelSize(self.config.font_size_base)

            # Update global application state
            if root_widget is None:
                if self.app:
                    self.app.setFont(font)
                    self.app.setStyleSheet(StyleFactory.get_app_qss(self.config))
                    for widget in self.app.topLevelWidgets():
                        self._refresh_recursive(widget, font)
            else:
                # If we're refreshing a specific widget, we don't necessarily want to
                # apply the FULL app QSS to it if it's already inherited,
                # but BaseWidget.apply_theme expects its own styling.
                # StyleFactory.get_app_qss might be too heavy for small widgets.
                # However, for now we keep existing behavior but optimized.
                root_widget.setStyleSheet(StyleFactory.get_app_qss(self.config))
                self._refresh_recursive(root_widget, font)
        except Exception as e:
            raise RuntimeError(f"Error in refresh_theme: {e}")

        finally:
            self._refreshing = False
            self._refreshed_widgets.clear()

    def _refresh_recursive(self, widget: QWidget, font: QFont) -> None:
        if not widget or id(widget) in self._refreshed_widgets:
            return

        self._refreshed_widgets.add(id(widget))

        # Handle Custom Application Widgets
        if self._is_custom_widget(widget):
            if hasattr(widget, "apply_theme"):
                # We expect custom apply_theme to NOT call refresh_theme again
                # OR if it does, it should check is_refreshing (handled in BaseWidget).
                widget.apply_theme()

        # Apply global font to all widgets to ensure inheritance and correct QFont metrics
        widget.setFont(font)

        # Standard Qt Widgets styling via helper
        self.apply_standard_widget_styles(widget)

        # Recurse for all children
        # findChildren(QWidget) is expensive, but FindDirectChildrenOnly is better.
        for child in widget.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            self._refresh_recursive(child, font)

    def apply_standard_widget_styles(self, widget: QWidget) -> None:
        """Applies consistent styling to standard Qt widgets based on their type."""
        if isinstance(widget, QListWidget):
            self.setup_list_widget(widget)
        elif isinstance(widget, QComboBox):
            self.setup_combo_box(widget)
        elif isinstance(widget, QTabBar):
            self.setup_tabs(widget)
        # elif isinstance(widget, QTabWidget):
        #     self.setup_tab_widget(widget)
        elif isinstance(widget, (QToolButton, QPushButton, QCheckBox, QRadioButton)):
            self.setup_button(widget)
        elif isinstance(widget, (QPlainTextEdit, QLineEdit, QSpinBox)):
            self.setup_input_widget(widget)

    def _is_custom_widget(self, widget: QWidget) -> bool:
        """Checks if the widget belongs to our internal source code namespace."""
        module_name = getattr(widget.__class__, "__module__", "")
        return module_name.startswith("MyVideoExplorer.")

    def get_icon(self, name: str, **kwargs: Any) -> QIcon:
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

        widget.setIconSize(
            QSize(self.config.size_standard_icon, self.config.size_standard_icon)
        )

    def setup_combo_box(self, widget: QComboBox) -> None:
        widget.setStyleSheet(StyleFactory.get_combo_qss(self.config))

    def setup_tabs(self, widget: QTabBar) -> None:
        widget.setStyleSheet(StyleFactory.get_tabs_qss(self.config))

    def setup_tab_widget(self, widget: QTabWidget) -> None:
        widget.setStyleSheet(StyleFactory.get_tabs_qss(self.config))

    def setup_button(self, widget: QAbstractButton) -> None:
        if isinstance(widget, (QPushButton, QToolButton)):
            object_name = widget.objectName()
            if object_name in (
                "folder_filter_media_nav_button",
                "media_info_toolbar_toggle_button",
                "media_info_toolbar_play_button",
            ):
                widget.setStyleSheet(StyleFactory.get_small_button_qss(self.config))
            else:
                widget.setStyleSheet(StyleFactory.get_button_qss(self.config))

    def setup_input_widget(self, widget: QPlainTextEdit | QLineEdit | QSpinBox) -> None:
        if isinstance(widget, QPlainTextEdit):
            # Check if it's the plot section text edit which needs a smaller font
            # Importing here to avoid circular dependencies if any
            # 4 is PLOT_SECTION_FONT_SIZE_OFFSET from media_info_section_plot
            is_plot_edit = False
            p = widget.parent()
            while p:
                if p.objectName() == "section_plot":
                    is_plot_edit = True
                    break
                p = p.parent()

            if is_plot_edit:
                # We need a new font object to avoid modifying the global one if it's shared
                font = QFont(widget.font())
                font.setPixelSize(max(1, self.config.font_size_base - 2))
                widget.setFont(font)
                # print(f"DEBUG: Applied plot font size {font.pixelSize()} to {widget}")

            widget.document().setDefaultFont(widget.font())
