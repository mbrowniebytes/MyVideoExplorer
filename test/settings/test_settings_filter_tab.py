from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton

from MyVideoExplorer.media_nav_search.filter_criteria_dialog import FilterCriteriaDialog
from MyVideoExplorer.settings.settings_filter_tab import SettingsFilterTab
from MyVideoExplorer.settings.settings_state import SettingsState


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
    buttons = [b for b in dialog.findChildren(QToolButton) if b.toolTip() == tooltip]
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


def test_add_filter_button_should_share_row_with_search_controls(tab):
    search_edit = tab._search_edit
    assert search_edit is not None
    add_buttons = [
        b for b in tab.findChildren(QToolButton) if b.toolTip() == "Add New Filter"
    ]
    assert len(add_buttons) == 1
    add_center = add_buttons[0].mapTo(tab, add_buttons[0].rect().center())
    search_center = search_edit.mapTo(tab, search_edit.rect().center())
    assert abs(add_center.y() - search_center.y()) <= search_edit.height()


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

    qtbot.mouseClick(delete_btn, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: state.delete_filter.called)
    state.delete_filter.assert_called_once_with("Alpha")


def test_dialog_delete_after_rename_should_delete_original_name(qtbot, tab, state):
    tab.open_edit_dialog(state.saved_filters[1])
    dialog = _active_dialog(tab)
    assert dialog._name_edit is not None
    dialog._name_edit.setText("Typed")

    qtbot.mouseClick(_dialog_button(dialog, "Delete Filter"), Qt.MouseButton.LeftButton)

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
