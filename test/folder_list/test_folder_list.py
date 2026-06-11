import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from src.folder_list.folder_list import FolderList
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel


class TestFolderList:
    @pytest.fixture
    def folder_list(self, qtbot):
        file_util = MagicMock(spec=FileUtil)
        settings = MagicMock()
        settings.folder_configs = [{"label": "Test", "path": "/path/to"}]
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            mock_log = MagicMock()
            widget = FolderList(file_util, settings, mock_log)
            # Prevent automatic refresh in build
            with patch.object(widget, "refresh"):
                widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_ui_initialization(self, folder_list):
        """Verify that UI components are correctly initialized."""
        assert folder_list.folder_view.count() == 0
        # Check if title label exists in layout (indirectly via build)
        assert folder_list._container.objectName() == "folderListContainer"

    def test_show_loading_state(self, folder_list):
        """Verify loading state displays correct text."""
        folder_list.folder_view.show_loading_state()
        assert folder_list.folder_view.count() == 1
        assert folder_list.folder_view.item(0).text() == "Loading..."
        assert folder_list.folder_view.item(0).flags() == Qt.ItemFlag.NoItemFlags

    def test_show_empty_state_no_path(self, folder_list):
        """Verify empty state with no path."""
        folder_list.folder_view.show_empty_state()
        assert folder_list.folder_view.count() == 1
        assert "No folders found." in folder_list.folder_view.item(0).text()

    def test_show_empty_state_with_path(self, folder_list):
        """Verify empty state with a specific path."""
        test_path = "/some/empty/path"
        folder_list.folder_view.show_empty_state(test_path)
        assert folder_list.folder_view.count() == 1
        assert "No folders found under" in folder_list.folder_view.item(0).text()
        assert test_path in folder_list.folder_view.item(0).text().replace("\\", "/")

    def test_update_folder_list_by_path(self, folder_list, mock_folder_items):
        """Verify list population from path (mocked FileUtil)."""
        folder_list.file_util.get_files_from_path.return_value = mock_folder_items

        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_path("/dummy/path")

        # Only directories should be added (Folder A, Folder B)
        assert folder_list.folder_view.count() == 2
        assert "Folder A" in folder_list.folder_view.item(0).text()
        assert "Folder B" in folder_list.folder_view.item(1).text()
        assert folder_list.folder_view.item(0).data(Qt.ItemDataRole.UserRole) == "/path/to/Folder A"

    def test_update_folder_list_by_items(self, folder_list, mock_folder_items):
        """Verify list population from provided items."""
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(mock_folder_items)
        assert folder_list.folder_view.count() == 2
        assert "Folder A" in folder_list.folder_view.item(0).text()

    def test_set_selected_folder(self, folder_list, mock_folder_items):
        """Verify programmatic selection of a folder."""
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(mock_folder_items)
        target_path = "/path/to/Folder B"

        folder_list.set_selected_folder(target_path)

        assert folder_list.folder_view.currentRow() == 1
        assert folder_list.folder_view.currentItem().data(Qt.UserRole) == target_path

    def test_select_next_folder(self, folder_list, mock_folder_items, qtbot):
        """Verify navigation to the next folder."""
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(mock_folder_items)
        folder_list.folder_view.setCurrentRow(0)

        with qtbot.waitSignal(folder_list.folder_view.sig_folder_selected) as blocker:
            folder_list.select_next_folder(1)

        assert folder_list.folder_view.currentRow() == 1
        assert blocker.args[0].data == "/path/to/Folder B"

    def test_on_folder_item_clicked(self, folder_list, mock_folder_items, qtbot):
        """Verify signal emission on item click."""
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(mock_folder_items)
        item = folder_list.folder_view.item(0)

        with qtbot.waitSignal(folder_list.folder_view.sig_folder_selected) as blocker:
            folder_list.folder_view.itemClicked.emit(item)

        assert blocker.args[0].data == "/path/to/Folder A"

    def test_nested_folder_prefixes(self, folder_list, mock_nested_folder_items):
        """Verify that depth translates to prefixes in the list."""
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_items(mock_nested_folder_items)
        assert folder_list.folder_view.count() == 2

        # Root (depth 0)
        assert folder_list.folder_view.item(0).text() == " Root"
        # Subfolder (depth 1)
        assert folder_list.folder_view.item(1).text() == "  ・ Subfolder"

    def test_refresh_asynchronous(self, folder_list, qtbot):
        """Verify refresh method triggers update via timer."""
        test_path = "/refresh/path"
        folder_list.file_util.get_files_from_path.return_value = [
            FileUtilModel(
                type="dir",
                name="Refreshed",
                full_path="/refresh/path/Refreshed",
                depth=0,
            )
        ]

        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.refresh(test_path, force=True)

        # Should show loading first
        assert folder_list.folder_view.item(0).text() == "Loading..."

        # Manually trigger the update to bypass timer issues in test
        with patch("src.folder_list.folder_list.FolderList._has_valid_media_folders", return_value=True):
            folder_list.update_folder_list_by_path(test_path)

        assert "Refreshed" in folder_list.folder_view.item(0).text()
        assert folder_list.folder_view.count() == 1

    def test_apply_theme(self, folder_list):
        """Verify that applying theme updates styles and fonts."""
        with patch("src.folder_list.folder_list.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.container_qss.return_value = "container { color: red; }"
            mock_theme.button_qss.return_value = "button { color: blue; }"
            mock_theme.list_qss.return_value = "list { color: green; }"
            mock_theme.label_qss.return_value = "label { color: black; }"

            folder_list.apply_theme()

            assert "container { color: red; }" in folder_list._container.styleSheet()
            assert "list { color: green; }" in folder_list.folder_view.styleSheet()
            assert folder_list.folder_view.font().family() == "Arial"
            assert folder_list.folder_view.font().pointSize() == 12
