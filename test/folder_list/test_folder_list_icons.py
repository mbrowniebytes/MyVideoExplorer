from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt

from MyVideoExplorer.folder_list.folder_list import FolderList
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel


class TestFolderListIcons:
    @pytest.fixture
    def folder_list(self, qtbot):
        file_util = MagicMock(spec=FileUtil)
        settings = MagicMock()
        settings.settings_data_model.folder_configs = [
            {"path": "/path/to/Folder A", "icon": "fa5s.video"},
            {"path": "/path/to/Folder B", "icon": "fa5s.image"},
        ]


        with patch("MyVideoExplorer.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            mock_log = MagicMock()
            widget = FolderList(file_util, settings=settings, log_util=mock_log)
            with patch.object(widget, "refresh"):
                widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_icons_assigned_on_initial_load(self, folder_list):
        items = [
            FileUtilModel(
                type="dir", name="Folder A", full_path="/path/to/Folder A", depth=0,
            ),
            FileUtilModel(
                type="dir", name="Folder B", full_path="/path/to/Folder B", depth=0
            ),
            FileUtilModel(
                type="dir", name="Folder C", full_path="/path/to/Folder C", depth=0
            ),
        ]
        with patch("MyVideoExplorer.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(items)

        assert folder_list.folder_list_view.count() == 3
        # Folder A should have video icon
        assert (
            folder_list.folder_list_view.item(0).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.video"
        )
        # Folder B should have image icon
        assert (
            folder_list.folder_list_view.item(1).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.image"
        )
        # Folder C should have default folder icon
        assert (
            folder_list.folder_list_view.item(2).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.folder"
        )

    def test_refresh_icons_updates_existing_items(self, folder_list):
        items = [
            FileUtilModel(
                type="dir", name="Folder A", full_path="/path/to/Folder A", depth=0
            ),
        ]
        with patch("MyVideoExplorer.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(items)
        assert (
            folder_list.folder_list_view.item(0).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.video"
        )

        # Change icon in settings
        folder_list.settings.settings_data_model.folder_configs[0]["icon"] = "fa5s.star"

        # Call refresh_icons
        folder_list.refresh_icons()

        # Verify it updated
        assert (
            folder_list.folder_list_view.item(0).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.star"
        )

    def test_refresh_icons_case_insensitivity(self, folder_list):
        items = [
            FileUtilModel(
                type="dir", name="Folder A", full_path="/PATH/TO/FOLDER A", depth=0
            ),
        ]
        with patch("MyVideoExplorer.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(items)

        # It should match /path/to/Folder A from settings despite casing
        assert (
            folder_list.folder_list_view.item(0).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.video"
        )

    def test_refresh_icons_no_change(self, folder_list):
        items = [
            FileUtilModel(
                type="dir", name="Folder A", full_path="/path/to/Folder A", depth=0
            ),
        ]
        with patch("MyVideoExplorer.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(items)

        # We'll just verify that calling refresh_icons doesn't break anything
        # and icon name remains the same.
        folder_list.refresh_icons()

        assert (
            folder_list.folder_list_view.item(0).data(Qt.ItemDataRole.UserRole + 1)
            == "fa5s.video"
        )
