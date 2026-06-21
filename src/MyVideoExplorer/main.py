#!/usr/bin/env python3
"""Main entry point for the application."""
import datetime
import sys
import traceback
from pathlib import Path
from PySide6 import QtAsyncio
from app.app_environment import IS_DEVELOPMENT

from PySide6.QtWidgets import (
    QApplication,
)

from app.app import App
from app.app_container import AppContainer


# Emergency fallback logging for when normal logging fails
def _emergency_log(message: str, exc_info: bool = False) -> None:
    """Write to log file immediately without relying on configured handlers."""
    log_dir = Path("log")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            # Try to get timestamp from event loop, but don't fail if it doesn't exist
            date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{date_str} - EMERGENCY - {message}\n")
            if exc_info:
                f.write(traceback.format_exc())
                f.write("\n")
            f.flush()
    except Exception:
        pass  # If emergency logging fails, nothing we can do


def main() -> int:
    """Application entry point."""
    container = None
    try:
        qapp = QApplication(sys.argv)

        # Create and configure logging FIRST, before anything else
        container = AppContainer()

        # Set up exception hooks BEFORE initializing the app UI
        sys.excepthook = container.log_util.handle_exception

        app = App(qapp, container)
        window = app.build()
        window.show()

        # Initialize state after showing window to avoid flicker
        app.initialize()

        # result = qapp.exec()
        result = QtAsyncio.run()

        container.log_util.log_memory("Application closing...")
        container.log_util.close()

        return result
    except Exception as e:
        # Emergency logging if container isn't initialized
        if container is None:
            _emergency_log(f"Exception during container initialization: {str(e)}", exc_info=True)
        else:
            # Container exists, use configured logging
            container.log_util.error(
                "Exception in main",
                extra_info={
                    "exc_type": type(e).__name__,
                    "exc_value": str(e),
                }
            )
            tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            container.log_util.error(f"{tb_str}")

        if IS_DEVELOPMENT:
            # dev, raise in ide
            raise e
    return -1

if __name__ == "__main__":
    sys.exit(main())
