from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication, QMainWindow

from MyVideoExplorer.app.app_state_handler import AppStateHandler
from MyVideoExplorer.utils.file_util import FileUtils


def test_app_state_handler_initialize_does_not_call_resize_window():
    QApplication.instance() or QApplication([])
    window = QMainWindow()
    container = MagicMock()
    container.settings.settings_data_model.media_configs = []
    container.settings.settings_data_model.auto_select_folder = (
        "auto_select_prior_folder"
    )
    container.settings.settings_data_model.prior_folder = ""

    handler = AppStateHandler(container, window)
    handler.initialize()

    container.controller.set_root_folders.assert_called_once_with([])
    container.controller.set_current_folder.assert_not_called()
    container.resize_window.assert_not_called()


def test_app_state_handler_restores_saved_prior_folder_on_startup(tmp_path):
    QApplication.instance() or QApplication([])
    root_folder = tmp_path / "media"
    prior_folder = root_folder / "Movies" / "Saved"
    prior_folder.mkdir(parents=True)

    window = QMainWindow()
    container = MagicMock()
    container.settings.settings_data_model.media_configs = [{"path": str(root_folder)}]
    container.settings.settings_data_model.auto_select_folder = (
        "auto_select_prior_folder"
    )
    container.settings.settings_data_model.prior_folder = str(prior_folder)

    handler = AppStateHandler(container, window)
    handler.initialize()

    container.controller.set_root_folders.assert_called_once_with(
        [FileUtils.normalize_path(root_folder)]
    )
    container.controller.set_current_folder.assert_called_once_with(
        FileUtils.normalize_path(prior_folder), force=True
    )
