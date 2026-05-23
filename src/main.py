#!/usr/bin/env python3
"""Main entry point for the application."""
import logging
import sys
import traceback

from PySide6.QtWidgets import (
    QApplication,
)

from src.app.app import App
from src.app.app_container import AppContainer


def main() -> int:
    """Application entry point."""
    try:
        qapp = QApplication(sys.argv)
        container = AppContainer()

        sys.excepthook = container.log_util.handle_exception

        app = App(qapp, container)
        window = app.build()
        window.show()

        result = qapp.exec()

        container.log_util.log_memory("Application closing...")
        container.log_util.close()

        return result
    except Exception as e:
        if getattr(sys, 'frozen', False):
            # deployed, log exception
            # date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            # log_file = f"log/app-{date_str}.log"
            log_file = "log/app.log"
            logging.root.handlers.clear()
            logging.basicConfig(
                filename=log_file,
                filemode="a",
                format="%(asctime)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d] %(extra)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                level=logging.INFO,
            )
            logging.error("exception in main", extra={"extra":traceback.format_exc()})
        else:
            # dev, just raise in ide
            raise e
    return -1

if __name__ == "__main__":
    sys.exit(main())
