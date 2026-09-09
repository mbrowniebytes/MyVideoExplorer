"""Application startup helper.

Contains the run() function that starts the QApplication, builds the App,
handles the loading splash, and performs top-level exception handling.
This module centralizes startup logic so main.py can remain a thin launcher.
"""

import datetime
import sys
import traceback
from pathlib import Path

from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication, QMainWindow

from MyVideoExplorer.app.app import App
from MyVideoExplorer.app.app_container import AppContainer
from MyVideoExplorer.app.app_environment import IS_DEVELOPMENT, ensure_required_directories
from MyVideoExplorer.app_loading.app_loading_controller import AppLoadingController
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.utils.log_util import LogUtil


def _emergency_log(message: str, exc_info: bool = False) -> None:
    """Fallback file logger used if configured logging isn't available."""
    try:
        log_dir = Path("log")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        with log_file.open("a", encoding="utf-8") as f:
            ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts} - EMERGENCY - {message}\n")
            if exc_info:
                f.write(traceback.format_exc())
                f.write("\n")
                f.flush()
    except Exception:
        # Nothing we can reasonably do if emergency logging fails
        pass


def run() -> int:
    """Run the application and return the process exit code."""
    container = None
    app_instance = None

    try:
        qapp = QApplication(sys.argv)
        ensure_required_directories()

        # Configure early logging and settings (used to decide whether to show splash)
        log_util = LogUtil.get_default().configure("error")
        settings_state = SettingsState(log_util)
        show_loading = getattr(settings_state, "show_loading_screen", True)

        loading_ctrl = None
        if show_loading:
            loading_ctrl = AppLoadingController()
            # Show top-level splash before creating the main window to avoid flicker
            loading_ctrl.show_top_level(None, qapp)

        # Create the main application window once
        window = QMainWindow()
        window.resize(800, 600)
        window.hide()

        if show_loading:
            # Suppress updates while building UI to avoid intermediate repaints
            window.setUpdatesEnabled(False)

        # Create container (sets up logging hooks, DI, etc.)
        container = AppContainer(window)
        sys.excepthook = container.log_util.handle_exception

        # Build and initialize the app UI off-screen
        app_instance = App(qapp, container, window)
        main_widget = app_instance.build()
        window.setCentralWidget(main_widget)
        app_instance.initialize()

        if show_loading and loading_ctrl is not None:
            window.setUpdatesEnabled(True)
            window.show()
            qapp.processEvents()
            loading_ctrl.remove(None, qapp)
        else:
            window.show()

        # Run the event loop integrated with asyncio
        exit_code = QtAsyncio.run()

        # Clean shutdown
        app_instance.close()
        return exit_code

    except Exception as exc:  # pragma: no cover - top-level guard
        if container is None:
            _emergency_log(f"Unhandled exception: {exc}", exc_info=True)
        else:
            try:
                container.log_util.error("Unhandled exception in main", extra_info={
                    "exc_type": type(exc).__name__,
                    "exc_value": str(exc),
                })
                tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                container.log_util.error(tb)
            except Exception:
                _emergency_log(f"Logging during exception failed: {exc}", exc_info=True)

        if IS_DEVELOPMENT:
            raise

    return -1
