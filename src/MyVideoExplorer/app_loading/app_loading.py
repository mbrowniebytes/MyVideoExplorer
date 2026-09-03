from __future__ import annotations
import random
from pathlib import Path

from typing import cast
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QResizeEvent
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QApplication,
    QGraphicsOpacityEffect,
    QGraphicsEffect,
)
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.lang.lang_loader import LangLoader


class AppLoadingWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_label = QLabel("MyVideoExplorer", parent=self)
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_label.setStyleSheet(APP_THEME.loading_label_qss())
        layout.addWidget(app_label)

        path_to_icon = FileUtil.get_resource_path("asset/app.png")
        pixmap = QPixmap()
        pixmap.loadFromData(Path(path_to_icon).read_bytes())
        pixmap = pixmap.scaled(
            512,
            512,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        icon_label = QLabel(parent=self)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        lang = LangLoader.get_lang("en")
        msg = random.choice(lang.loading_messages)
        loading_label = QLabel(msg, parent=self)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet(APP_THEME.loading_label_qss())
        layout.addWidget(loading_label)

    def setup_window(self, window: QMainWindow | None, app: QApplication) -> None:
        if window:
            window.setWindowTitle("MyVideoExplorer")
        path_to_icon = FileUtil.get_resource_path("asset/app.png")
        pixmap = QPixmap()
        pixmap.loadFromData(Path(path_to_icon).read_bytes())
        appIcon = QIcon(pixmap)
        app.setWindowIcon(appIcon)

    def show_temporary_central(self, window: QMainWindow, app: QApplication) -> None:
        """DEPRECATED: kept for compatibility. Use show_splash instead.

        Make this loading widget the temporary central widget and paint it.
        """
        self.show_splash(window, app)

    def show_splash(self, main_window: QMainWindow | None, app: QApplication) -> None:
        """Show this loading widget as a top-level splash window centered over the main window.

        If main_window is None, center on the primary screen. This avoids creating or
        showing the main QMainWindow before it's ready and prevents a small native window
        from briefly appearing.
        """
        # Ensure top-level
        self.setParent(None)
        # Keep window decoration hidden for a clean splash look
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        # Allow translucent backgrounds if supported
        try:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        except Exception:
            pass

        # Setup window properties (title/icon) using the main window context if present
        try:
            self.setup_window(main_window, app)
        except Exception:
            try:
                # Best-effort: try with a temporary QMainWindow context
                tmp = None
                self.setup_window(tmp, app)
            except Exception:
                pass

        # Position & size: match main_window size and center over it, or center on screen
        try:
            if main_window is not None:
                main_geo = main_window.frameGeometry()
                self.resize(main_geo.width(), main_geo.height())
                self.move(main_geo.left(), main_geo.top())
            else:
                raise RuntimeError("no main window")
        except Exception:
            # fallback: center on primary screen
            screen = app.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                w = min(800, geo.width())
                h = min(600, geo.height())
                x = geo.left() + (geo.width() - w) // 2
                y = geo.top() + (geo.height() - h) // 2
                self.setGeometry(x, y, w, h)

        self.show()
        app.processEvents()

    def create_overlay_with_main(self, window: QMainWindow, main_widget: QWidget, app: QApplication) -> QWidget:
        """Create an overlay container containing the main widget with this loading widget on top.

        Returns the container widget which owns both child widgets.
        """
        # Make the container a child of the main window so it lives inside the window's stacking order
        container_widget = QWidget(window)
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(main_widget)

        # Reparent the loading widget into the container so it overlays the main UI
        # Also clear any window flags that would keep the splash as a top-level on-top window
        try:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.setWindowFlag(Qt.WindowType.Window, False)
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)
        except Exception:
            pass

        self.setParent(container_widget)
        self.raise_()
        self.show()

        window.setCentralWidget(container_widget)

        # Ensure layout geometry is established before sizing the overlay
        # Avoid forcing an extra show() of the window here; the caller controls when to show
        app.processEvents()

        try:
            self.setGeometry(container_widget.rect())
        except Exception:
            pass

        # Keep overlay sized on container resize
        try:
            _orig_resize = container_widget.resizeEvent
        except Exception:
            _orig_resize = None

        def _on_container_resize(event: QResizeEvent) -> None:
            try:
                self.setGeometry(container_widget.rect())
            except Exception:
                pass
            if _orig_resize:
                _orig_resize(event)

        container_widget.resizeEvent = _on_container_resize # type: ignore

        return container_widget

    def fade_and_remove(self, container_widget: QWidget | None, app: QApplication, duration: int = 750) -> None:
        """Fade out this loading overlay and remove it, revealing the main UI."""
        try:
            effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(effect)
            effect.setOpacity(1.0)

            anim = QPropertyAnimation(effect, b"opacity")
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setDuration(duration)
            anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

            # Keep a reference on the splash to avoid GC while running
            self._startup_anim = anim

            def _on_fade_finished():
                try:
                    # If this was an overlay inside the main window, update that container
                    if container_widget is not None:
                        try:
                            self.setParent(None)
                        except Exception:
                            pass
                        try:
                            self.deleteLater()
                        except Exception:
                            pass
                        try:
                            self.setGraphicsEffect(cast(QGraphicsEffect, None))
                        except Exception:
                            pass
                        try:
                            container_widget.update()
                        except Exception:
                            pass
                    else:
                        # Top-level splash: hide and delete
                        try:
                            self.hide()
                        except Exception:
                            pass
                        try:
                            self.close()
                        except Exception:
                            pass
                        try:
                            self.deleteLater()
                        except Exception:
                            pass
                    app.processEvents()
                except Exception:
                    pass

            anim.finished.connect(_on_fade_finished)
            QTimer.singleShot(50, anim.start)
        except Exception:
            # Fallback: remove immediately
            try:
                if container_widget is not None:
                    self.setParent(None)
                    self.deleteLater()
                else:
                    self.close()
                app.processEvents()
            except Exception:
                pass
