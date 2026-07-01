from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.folder_list.folder_list import FolderList
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel

class TestFolderListRandom:
    @pytest.fixture
    def folder_list(self, qtbot):
        file_util = MagicMock(spec=FileUtil)
        settings = MagicMock()
        settings.settings_data_model.folder_configs = []

        mock_log = MagicMock()

        with patch("MyVideoExplorer.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            widget = FolderList(file_util, settings=settings, log_util=mock_log)
            widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_random_button_initial_state(self, folder_list):
        """Verify that random button is disabled initially."""
        assert folder_list.random_folder_button is not None
        assert not folder_list.random_folder_button.isEnabled()

    def test_random_button_enabled_when_folders_present(self, folder_list):
        """Verify that random button is enabled when folders are loaded."""
        items = [
            FileUtilModel(type="dir", name="Folder A", full_path="/path/A", depth=0),
        ]
        folder_list.update_folder_list_by_items(items)
        assert folder_list.random_folder_button.isEnabled()

    def test_random_button_disabled_when_empty(self, folder_list):
        """Verify that random button is disabled when list is cleared."""
        items = [
            FileUtilModel(type="dir", name="Folder A", full_path="/path/A", depth=0),
        ]
        folder_list.update_folder_list_by_items(items)
        assert folder_list.random_folder_button.isEnabled()

        folder_list.update_folder_list_by_items([])
        assert not folder_list.random_folder_button.isEnabled()

    def test_random_folder_navigation(self, folder_list, qtbot):
        """Verify that clicking random button emits navigation signal."""
        items = [
            FileUtilModel(type="dir", name="Folder A", full_path="/path/A", depth=0),
            FileUtilModel(type="dir", name="Folder B", full_path="/path/B", depth=0),
        ]
        folder_list.update_folder_list_by_items(items)

        with qtbot.waitSignal(folder_list.sig_navigate_to_folder) as blocker:
            folder_list.random_folder_button.click()

        assert blocker.args[0] in ["/path/A", "/path/B"]
