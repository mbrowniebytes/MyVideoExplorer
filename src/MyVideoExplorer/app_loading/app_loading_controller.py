"""Controller wrapper for AppLoadingWidget.

Provides a minimal public API to show the splash, create overlays, and remove the splash.
This separates lifecycle operations from the widget implementation.
"""
from __future__ import annotations
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from MyVideoExplorer.app_loading.app_loading import AppLoadingWidget


class AppLoadingController:
    """Small helper that encapsulates common splash operations.

    This keeps callers from manipulating AppLoadingWidget directly and centralizes
    the lifecycle (show -> optionally overlay -> fade/remove).
    """

    def __init__(self, widget: AppLoadingWidget | None = None) -> None:
        self._widget = widget or AppLoadingWidget()

    def show_top_level(self, main_window: QMainWindow | None, app: QApplication) -> None:
        """Show the splash as a top-level transient window."""
        self._widget.show_splash(main_window, app)

    def create_overlay(self, window: QMainWindow, main_widget: QWidget, app: QApplication) -> QWidget:
        """Create an overlay container that hosts the main widget with the splash on top.

        Returns the created container widget.
        """
        return self._widget.create_overlay_with_main(window, main_widget, app)

    def remove(self, container_widget: QWidget | None, app: QApplication, duration: int = 500) -> None:
        """Fade and remove the splash, either top-level (container_widget is None) or overlay."""
        self._widget.fade_and_remove(container_widget, app, duration)
