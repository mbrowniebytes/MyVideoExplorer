from __future__ import annotations

from unittest.mock import MagicMock

import duckdb
import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QMessageBox, QToolButton

from MyVideoExplorer.db.db_filters import DbFilters
from MyVideoExplorer.media_nav_search.filter_criteria_dialog import FilterCriteriaDialog
from MyVideoExplorer.settings.settings_filter_tab import SettingsFilterTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton


@pytest.fixture
def state():
    mock_state = MagicMock(spec=SettingsState)
    mock_state.media_configs = []
    mock_state.tags = []
    mock_state.saved_filters = [
        {"name": "Alpha", "filters": [{"filter": "Folder", "value": "abc"}]},
        {"name": "Beta", "filters": [{"filter": "Title", "value": "xyz"}]},
    ]
    return mock_state


@pytest.fixture
def tab(qtbot, state):
    widget = SettingsFilterTab(state, MagicMock())
    qtbot.addWidget(widget)
    widget.resize(700, 500)
    widget.show()
    qtbot.waitExposed(widget)
    return widget


def _active_dialog(tab: SettingsFilterTab) -> FilterCriteriaDialog:
    dialog = tab._active_dialog
    assert dialog is not None
    return dialog


def _dialog_button(dialog: FilterCriteriaDialog, tooltip: str) -> QToolButton:
    buttons = [
        b for b in dialog.findChildren(QToolButton) if b.toolTip().startswith(tooltip)
    ]
    assert buttons, f"button '{tooltip}' not found"
    return buttons[0]


def test_filter_rows_with_saved_filters_should_have_edit_left_and_delete_right(tab):
    table = tab._filter_table_widget
    assert table is not None
    assert table.rowCount() == 2

    edit_btn = table.cellWidget(0, SettingsFilterTab.COL_EDIT)
    delete_btn = table.cellWidget(0, SettingsFilterTab.COL_DELETE)
    assert isinstance(edit_btn, QToolButton)
    assert isinstance(delete_btn, QToolButton)
    assert "Edit" in edit_btn.toolTip()
    assert "Delete" in delete_btn.toolTip()
    assert SettingsFilterTab.COL_EDIT < SettingsFilterTab.COL_NAME
    assert SettingsFilterTab.COL_DELETE == table.columnCount() - 1
    assert table.wordWrap() is False
    assert table.textElideMode() == Qt.TextElideMode.ElideRight
    assert (
        table.horizontalHeaderItem(SettingsFilterTab.COL_COUNT).text()
        == "Media Folder Count"
    )
    assert isinstance(table.cellWidget(0, SettingsFilterTab.COL_REFRESH), QToolButton)


def test_movie_count_column_should_display_cached_count_and_be_sortable(tab, state):
    state.saved_filters[0]["total_count"] = 12
    state.saved_filters[1]["total_count"] = 4
    tab._refresh_filter_list()

    table = tab._filter_table_widget
    assert table is not None
    assert table.item(0, SettingsFilterTab.COL_COUNT).text() == "12"
    assert table.horizontalHeader().isSortIndicatorShown()
    tab._on_sort_changed(SettingsFilterTab.COL_COUNT, Qt.SortOrder.DescendingOrder)
    assert table.item(0, SettingsFilterTab.COL_NAME).text() == "Alpha"
    assert table.item(1, SettingsFilterTab.COL_NAME).text() == "Beta"
    tab._on_sort_changed(SettingsFilterTab.COL_COUNT, Qt.SortOrder.AscendingOrder)
    assert table.item(0, SettingsFilterTab.COL_NAME).text() == "Beta"


def test_criteria_count_column_should_be_sortable(tab, state):
    state.saved_filters = [
        {"name": "Few", "filters": [{"filter": "title", "value": "one"}]},
        {
            "name": "Many",
            "filters": [
                {"filter": "title", "value": "one"},
                {"filter": "genre", "value": "drama"},
                {"filter": "year", "value": "2000"},
            ],
        },
        {
            "name": "Some",
            "filters": [
                {"filter": "title", "value": "one"},
                {"filter": "genre", "value": "drama"},
            ],
        },
    ]
    tab._refresh_filter_list()

    table = tab._filter_table_widget
    assert table is not None
    assert table.horizontalHeaderItem(SettingsFilterTab.COL_CRITERIA_COUNT).text() == (
        "Criteria Count"
    )
    tab._on_sort_changed(
        SettingsFilterTab.COL_CRITERIA_COUNT, Qt.SortOrder.AscendingOrder
    )
    assert [
        table.item(row, SettingsFilterTab.COL_NAME).text()
        for row in range(table.rowCount())
    ] == ["Few", "Some", "Many"]
    tab._on_sort_changed(
        SettingsFilterTab.COL_CRITERIA_COUNT, Qt.SortOrder.DescendingOrder
    )
    assert [
        table.item(row, SettingsFilterTab.COL_NAME).text()
        for row in range(table.rowCount())
    ] == ["Many", "Some", "Few"]


def test_movie_count_column_should_reflect_selected_media_folders(qtbot, tmp_path):
    state = MagicMock(spec=SettingsState)
    state.media_configs = [
        {"path": "/media/a"},
        {"path": "/media/b"},
    ]
    state.selected_media_folders = ["/media/a"]
    state.tags = []
    store = DbFilters(
        state,
        tmp_path / "filters.db",
    )
    store.replace_all([{"name": "Selected", "filters": []}])
    with duckdb.connect(store.path_utils.normalize_path(store.db_path)) as con:
        con.execute(
            "UPDATE media_filters SET folder_counts = map(['/media/a', '/media/b'], [3, 7]), "
            "total_count = 10 WHERE name = 'Selected'"
        )
    state.filter_store = store
    state.saved_filters = store.list_filters()

    tab = SettingsFilterTab(state, MagicMock())
    qtbot.addWidget(tab)

    table = tab._filter_table_widget
    assert table is not None
    count_item = table.item(0, SettingsFilterTab.COL_COUNT)
    assert count_item is not None
    assert count_item.text() == "3"


def test_delete_filter_with_more_than_ten_matches_should_require_confirmation(
    qtbot, tab, state, monkeypatch
):
    state.saved_filters[0]["total_count"] = 11
    answers = [QMessageBox.StandardButton.No]
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_filter_tab.QMessageBox.question",
        lambda *args, **kwargs: answers.pop(0),
    )

    tab._request_delete("Alpha")
    assert not state.delete_filter.called

    answers.append(QMessageBox.StandardButton.Yes)
    tab._request_delete("Alpha")
    qtbot.waitUntil(lambda: state.delete_filter.called)
    state.delete_filter.assert_called_once_with("Alpha")


def test_row_refresh_button_should_update_movie_count_off_gui_thread(qtbot, tmp_path):
    media_db = tmp_path / "media.db"
    from MyVideoExplorer.db.db_migrations import DbMigrations

    DbMigrations(str(media_db)).run_migrations()
    with duckdb.connect(media_db.as_posix()) as con:
        con.execute(
            "INSERT INTO media_file (id, media_path, file_path, type, title) VALUES "
            "(1, '/media', '/media/Movie/movie.mkv', 'video', 'Movie')"
        )

    state = MagicMock(spec=SettingsState)
    state.media_configs = [{"path": "/media"}]
    state.selected_media_folders = []
    state.tags = []
    state.get_db_path.side_effect = lambda _config: media_db.as_posix()
    store = DbFilters(
        state,
        tmp_path / "filters.db",
    )
    store.replace_all([{"name": "All Movies", "filters": []}])
    state.filter_store = store
    state.saved_filters = store.list_filters()
    state.load_filters.side_effect = lambda: setattr(
        state, "saved_filters", store.list_filters()
    )

    tab = SettingsFilterTab(state, MagicMock())
    qtbot.addWidget(tab)
    table = tab._filter_table_widget
    assert table is not None
    refresh_button = table.cellWidget(0, SettingsFilterTab.COL_REFRESH)
    assert isinstance(refresh_button, QToolButton)
    qtbot.mouseClick(refresh_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: tab._active_count_worker is None)

    refreshed = store.get_filter("All Movies")
    assert refreshed is not None
    assert refreshed["total_count"] == 1
    count_item = table.item(0, SettingsFilterTab.COL_COUNT)
    assert count_item is not None
    assert count_item.text() == "1"


def test_add_filter_button_should_share_row_with_search_controls(tab):
    search_edit = tab._search_edit
    assert search_edit is not None
    refresh_button = tab._refresh_all_btn
    assert refresh_button is not None
    assert refresh_button.toolTip() == "Update all Filter Media counts"
    add_buttons = [
        b for b in tab.findChildren(QToolButton) if b.toolTip() == "Add New Filter"
    ]
    assert len(add_buttons) == 1
    add_center = add_buttons[0].mapTo(tab, add_buttons[0].rect().center())
    search_center = search_edit.mapTo(tab, search_edit.rect().center())
    assert abs(add_center.y() - search_center.y()) <= search_edit.height()
    refresh_center = refresh_button.mapTo(tab, refresh_button.rect().center())
    assert refresh_center.x() < add_center.x()
    progress_bar = tab._bulk_progress_bar
    assert progress_bar is not None
    assert progress_bar.parentWidget() is refresh_button.parentWidget()
    add_x_before = add_buttons[0].mapTo(tab, add_buttons[0].rect().topLeft()).x()
    progress_bar.show()
    button_pos = refresh_button.mapTo(tab, refresh_button.rect().topLeft())
    progress_pos = progress_bar.mapTo(tab, progress_bar.rect().topLeft())
    assert progress_pos.x() == button_pos.x()
    assert (
        progress_pos.y() + progress_bar.height()
        == button_pos.y() + refresh_button.height()
    )
    assert (
        add_buttons[0].mapTo(tab, add_buttons[0].rect().topLeft()).x() == add_x_before
    )


def test_edit_button_click_should_open_non_blocking_dialog(qtbot, tab):
    table = tab._filter_table_widget
    assert table is not None
    edit_btn = table.cellWidget(1, SettingsFilterTab.COL_EDIT)
    assert isinstance(edit_btn, QToolButton)

    qtbot.mouseClick(edit_btn, Qt.MouseButton.LeftButton)

    dialog = _active_dialog(tab)
    assert dialog.isVisible()
    assert dialog.original_name == "Beta"
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    dialog.reject()


def test_dialog_save_after_rename_should_persist_with_original_name(qtbot, tab, state):
    table = tab._filter_table_widget
    assert table is not None
    table.selectRow(0)
    tab._on_double_click(table.model().index(0, SettingsFilterTab.COL_NAME))
    dialog = _active_dialog(tab)
    assert dialog._name_edit is not None
    dialog._name_edit.setText("Alpha Renamed")

    qtbot.mouseClick(_dialog_button(dialog, "Save"), Qt.MouseButton.LeftButton)

    # Persistence is deferred until after the dialog has closed
    assert not dialog.isVisible()
    qtbot.waitUntil(lambda: state.save_filter.called)
    state.save_filter.assert_called_once_with(
        "Alpha Renamed",
        [{"filter": "Folder", "value": "abc"}],
        original_name="Alpha",
    )


def test_row_delete_button_should_delete_filter(qtbot, tab, state):
    table = tab._filter_table_widget
    assert table is not None
    delete_btn = table.cellWidget(0, SettingsFilterTab.COL_DELETE)
    assert isinstance(delete_btn, QToolButton)

    delete_btn.enterEvent(QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1)))
    qtbot.waitUntil(lambda: delete_btn.is_armed, timeout=3000)
    qtbot.mouseClick(delete_btn, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: state.delete_filter.called)
    state.delete_filter.assert_called_once_with("Alpha")


def test_dialog_delete_after_rename_should_delete_original_name(qtbot, tab, state):
    tab.open_edit_dialog(state.saved_filters[1])
    dialog = _active_dialog(tab)
    assert dialog._name_edit is not None
    dialog._name_edit.setText("Typed")

    delete_btn = _dialog_button(dialog, "Delete Filter")
    delete_btn.enterEvent(QEnterEvent(QPointF(1, 1), QPointF(1, 1), QPointF(1, 1)))
    qtbot.waitUntil(
        lambda: isinstance(delete_btn, DelayedDeleteButton) and delete_btn.is_armed,
        timeout=3000,
    )
    qtbot.mouseClick(delete_btn, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: state.delete_filter.called)
    state.delete_filter.assert_called_once_with("Beta")


def test_add_mode_save_should_create_new_filter_with_added_criteria(qtbot, tab, state):
    tab.open_add_filter()
    dialog = _active_dialog(tab)
    combo = dialog._criteria_type_combo
    table = dialog._filter_table
    assert combo is not None
    assert table is not None
    assert dialog._name_edit is not None

    combo.setCurrentText("    Folder")
    qtbot.mouseClick(_dialog_button(dialog, "Add Criteria"), Qt.MouseButton.LeftButton)
    # The new value cell editor is open; type without committing it
    editor = table.indexWidget(table.currentIndex())
    assert editor is not None
    qtbot.keyClicks(editor, "movies")
    dialog._name_edit.setText("New One")

    qtbot.mouseClick(_dialog_button(dialog, "Save"), Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: state.save_filter.called)
    state.save_filter.assert_called_once_with(
        "New One", [{"filter": "Folder", "value": "movies"}], original_name=None
    )


def test_save_with_empty_name_should_keep_dialog_open(qtbot, tab, state):
    tab.open_add_filter()
    dialog = _active_dialog(tab)

    qtbot.mouseClick(_dialog_button(dialog, "Save"), Qt.MouseButton.LeftButton)

    assert dialog.isVisible()
    assert not state.save_filter.called
    dialog.reject()


def test_readonly_dialog_should_hide_add_criteria_and_action_buttons(qtbot):
    dialog = FilterCriteriaDialog(
        genres=[],
        media_configs=[],
        filter_name="RO",
        filters=[{"filter": "Folder", "value": "abc"}],
        edit_mode=False,
        readonly=True,
    )
    qtbot.addWidget(dialog)

    tooltips = {b.toolTip() for b in dialog.findChildren(QToolButton)}
    assert dialog._criteria_type_combo is None
    assert "Add Criteria" not in tooltips
    assert "Save" not in tooltips
    assert "Delete Filter" not in tooltips
