from __future__ import annotations

import gc
from unittest.mock import MagicMock, patch

import pytest
import shiboken6
from PySide6.QtCore import Qt

from MyVideoExplorer.folder_list.folder_list_view import FolderListView
from MyVideoExplorer.utils.file_util_model import FileUtilModel


def _folders(count: int) -> list[FileUtilModel]:
    return [
        FileUtilModel(type="dir", name=f"Folder {i}", full_path=f"/root/Folder {i}")
        for i in range(count)
    ]


class TestFolderListView:
    @pytest.fixture
    def view(self, qtbot):
        widget = FolderListView(log_util=MagicMock())
        qtbot.addWidget(widget)
        return widget

    def test_clear_items_with_items_should_hand_items_back_to_python(self, view):
        view.populate_view(_folders(3))
        view.setCurrentRow(1)
        items = [view.item(row) for row in range(view.count())]

        view.clear_items()

        assert view.count() == 0
        assert view.currentRow() == -1
        # Detached from the list, so Python (not Qt) deletes them
        assert all(shiboken6.isValid(item) for item in items)
        assert all(item.listWidget() is None for item in items)

    def test_rebuild_states_should_not_use_qlistwidget_clear(self, view):
        # QListWidget.clear() left stale item wrappers that crashed the app
        with patch.object(view, "clear", side_effect=AssertionError("clear used")):
            view.populate_view(_folders(2))
            view.show_loading_state(["/root"])
            view.show_empty_state(message="Nothing here")
            view.populate_view(_folders(2))

        assert view.count() == 2

    def test_repeated_loading_and_populate_with_gc_should_keep_items_consistent(
        self, view
    ):
        # Mirrors a filter save: loading state twice, then repopulate
        for _ in range(25):
            view.show_loading_state(["/root"])
            view.show_loading_state(["/root"])
            view.populate_view(_folders(5))
            view.set_selected_folder("/root/Folder 2")
            gc.collect()

        assert view.count() == 5
        assert view.currentRow() == 2
        assert view.item(4).data(Qt.ItemDataRole.UserRole) == "/root/Folder 4"
