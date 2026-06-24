from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt

from MyVideoExplorer.file_list.file_list import FileList
from MyVideoExplorer.utils.file_util import FileUtil


class TestFileList:
    @pytest.fixture
    def file_list(self, qtbot):
        file_util = MagicMock(spec=FileUtil)
        mock_log = MagicMock()
        widget = FileList(file_util, mock_log)
        widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_ui_initialization(self, file_list):
        """Verify that UI components are correctly initialized."""
        assert file_list.file_list_view.count() == 0
        assert file_list._container is not None
        # Check title label text indirectly if possible or by accessing it if it was stored
        # Since it's not stored as an attribute, we'd have to find it in the layout
        # Note: _container might be the one containing labels
        labels = file_list._container.findChildren(
            pytest.importorskip("PySide6.QtWidgets").QLabel
        )
        assert any("Folder Contents:" in label.text() for label in labels)

    def test_update_file_list(self, file_list, mock_file_items):
        """Verify list population from path (mocked FileUtil)."""
        file_list.file_util.get_child_files.return_value = mock_file_items

        file_list.update_file_list("/dummy/path")

        assert file_list.file_list_view.count() == 3
        assert "video1.mp4" in file_list.file_list_view.item(0).text()
        assert "video2.mkv" in file_list.file_list_view.item(1).text()
        assert "readme.txt" in file_list.file_list_view.item(2).text()
        assert (
            file_list.file_list_view.item(0).data(Qt.ItemDataRole.UserRole)
            == "/path/to/video1.mp4"
        )
        assert "Files in folder: 3" in file_list.help_icon.toolTip()
        # The formatting might have changed slightly due to whitespace/newlines
        assert "File List Usage:" in file_list.help_icon.toolTip()

    def test_set_selected_file(self, file_list, mock_file_items):
        """Verify programmatic selection of a file."""
        file_list.file_util.get_child_files.return_value = mock_file_items
        file_list.update_file_list("/dummy/path")

        target_path = "/path/to/video2.mkv"
        file_list.set_selected_file(target_path)

        assert file_list.file_list_view.currentRow() == 1
        assert (
            file_list.file_list_view.currentItem().data(Qt.ItemDataRole.UserRole)
            == target_path
        )

    def test_emit_file_selected(self, file_list, mock_file_items, qtbot):
        """Verify signal emission on item click."""
        file_list.file_util.get_child_files.return_value = mock_file_items
        file_list.update_file_list("/dummy/path")

        item = file_list.file_list_view.item(0)

        with qtbot.waitSignal(file_list.sig_file_selected_intent) as blocker:
            file_list.file_list_view.itemClicked.emit(item)

        assert blocker.args[0].data == "/path/to/video1.mp4"

    def test_refresh(self, file_list, mock_file_items):
        """Verify refresh calls update_file_list."""
        file_list.file_util.get_child_files.return_value = mock_file_items

        file_list.refresh("/refresh/path")

        file_list.file_util.get_child_files.assert_called_with("/refresh/path")
        assert file_list.file_list_view.count() == 3

    def test_apply_theme(self, file_list):
        """Verify that applying theme updates styles and fonts."""
        with (
            patch("MyVideoExplorer.file_list.file_list_view.APP_THEME") as mock_theme_view,
            patch("MyVideoExplorer.file_list.file_list.APP_THEME") as mock_theme_list,
        ):

            for mock_theme in [mock_theme_view, mock_theme_list]:
                mock_theme.font_family = "Arial"
                mock_theme.font_size = 14
                mock_theme.container_qss.return_value = "container { color: blue; }"
                mock_theme.list_qss.return_value = "list { color: yellow; }"
                mock_theme.label_qss.return_value = "label { color: green; }"
                mock_theme.small_button_qss.return_value = "button { color: red; }"

            file_list.apply_theme()

            assert "container { color: blue; }" in file_list._container.styleSheet()
            assert "list { color: yellow; }" in file_list.file_list_view.styleSheet()
            assert file_list.file_list_view.font().family() == "Arial"
            assert file_list.file_list_view.font().pointSize() == 14
