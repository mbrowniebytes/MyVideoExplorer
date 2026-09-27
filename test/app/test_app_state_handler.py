from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication, QMainWindow

from MyVideoExplorer.app.app_state_handler import AppStateHandler


def test_app_state_handler_initialize_does_not_call_resize_window():
    QApplication.instance() or QApplication([])
    window = QMainWindow()
    container = MagicMock()
    container.settings.settings_data_model.media_configs = []

    handler = AppStateHandler(container, window)
    handler.initialize()

    container.controller.set_root_folders.assert_called_once_with([])
    container.resize_window.assert_not_called()
