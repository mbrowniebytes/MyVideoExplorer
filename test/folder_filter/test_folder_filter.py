from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel, QToolButton

from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.folder_filter.folder_filter_table import (
    FilterTagCloudWidget,
    FolderFilterTable,
)
from MyVideoExplorer.settings.settings_filter_tab import SettingsFilterTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class TestFolderNavFilters:
    @pytest.fixture
    def settings_mock(self):
        settings = MagicMock()
        settings.settings_data_model.media_configs = [
            {"label": "Movies", "path": "movies"},
            {"label": "TV Shows", "path": "tv"},
        ]
        settings.settings_data_model.saved_filters = []
        settings.settings_data_model.tags = [
            {"tag": "Action", "color": "#ff0000"},
            {"tag": "Sci-Fi", "color": "#00ff00"},
            {"tag": "Favorite", "color": "#0000ff"},
        ]
        settings.settings_data_model.tag_store = None
        settings.saved_filters = []
        settings.tag_store = None
        return settings

    @pytest.fixture
    def nav_filters(self, qtbot, settings_mock):
        file_util = MagicMock(spec=FileUtil)
        nfo_util = MagicMock(spec=NfoParseUtil)
        engine = FolderFilterFilter(nfo_util, settings_mock.settings_data_model)
        engine.apply_filters = MagicMock(side_effect=engine.apply_filters)
        mock_log = MagicMock()
        widget = FolderFilters(engine, file_util, settings_mock, mock_log)
        widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_ui_initialization(self, nav_filters):
        """Verify that UI components are correctly initialized."""
        assert nav_filters.apply_button.toolTip().strip() == "Apply Filters"
        assert nav_filters.tag_button.toolTip().strip() == "Tags"
        assert nav_filters.saved_filters_combo.count() >= 1
        assert (
            nav_filters.saved_filters_combo.itemText(0)
            == "- Showing All - Select a Filter -"
        )
        # Starts with 1 row (placeholder)
        assert nav_filters.filter_table.rowCount() == 1
        placeholder = nav_filters.filter_table.cellWidget(0, 0)
        assert (
            placeholder.text()
            if placeholder
            else nav_filters.filter_table.item(0, 0).text()
        ) == "Select a filter from above dropdown"
        assert nav_filters.filter_table.columnCount() == 2
        assert nav_filters.filter_table.readonly is True

    def test_add_remove_selected_tag(self, nav_filters):
        """Verify adding and removing selected tags."""
        nav_filters.show()
        assert len(nav_filters.selected_tags) == 0
        assert not nav_filters.selected_tags_container.isVisible()

        # Add a tag
        nav_filters.add_selected_tag("Action")
        assert nav_filters.selected_tags == ["Action"]
        assert nav_filters.selected_tags_container.isVisible()
        assert nav_filters.selected_tags_layout.count() == 1

        # Adding duplicate does not duplicate
        nav_filters.add_selected_tag("action")
        assert len(nav_filters.selected_tags) == 1

        # Add another tag
        nav_filters.add_selected_tag("Sci-Fi")
        assert len(nav_filters.selected_tags) == 2
        assert nav_filters.selected_tags_layout.count() == 2

        # Click tag button to remove
        tag_btn = nav_filters.selected_tags_layout.itemAt(0).widget()
        tag_btn.click()
        assert nav_filters.selected_tags == ["Sci-Fi"]
        assert nav_filters.selected_tags_layout.count() == 1

        # Remove remaining tag
        nav_filters.remove_selected_tag("Sci-Fi")
        assert len(nav_filters.selected_tags) == 0
        assert not nav_filters.selected_tags_container.isVisible()

    def test_collect_filters_with_tags(self, nav_filters):
        """Verify that filters and tags are collected."""
        nav_filters.filter_table.add_filter("Folder", "test_folder")
        nav_filters.add_selected_tag("4K")

        mock_items = []
        nav_filters._apply_filters_internal(mock_items)

        # Check that apply_filters was called with both table filter and tag filter
        call_args = nav_filters.folder_nav_filters_filter.apply_filters.call_args
        filters = call_args[1]["filters"]
        assert any(
            f["filter"] == "Folder" and f["value"] == "test_folder" for f in filters
        )
        assert any(f["filter"] == "Tag" and f["value"] == "4K" for f in filters)

    def test_apply_filters_trigger(self, nav_filters, qtbot):
        """Verify that clicking apply button emits signal."""
        nav_filters.settings.settings_data_model.db_enabled.return_value = False
        with qtbot.waitSignal(nav_filters.filters_requested) as blocker:
            nav_filters.apply_button.click()
        assert blocker.args is not None

    def test_filter_criteria_button_opens_popup_with_criteria_table(
        self, nav_filters
    ):
        assert nav_filters.filter_criteria_button.toolTip() == "View Filter Criteria"
        assert not nav_filters.filter_criteria_button.icon().isNull()

        nav_filters.filter_table.add_filter("Folder", "my_movie")
        nav_filters.filter_criteria_button.click()

        assert nav_filters._criteria_popup is not None
        assert nav_filters._criteria_popup.isVisible()
        assert (
            nav_filters._criteria_popup.findChild(FolderFilterTable)
            is nav_filters.filter_table
        )
        assert nav_filters.filter_table.collect_filters() == [
            {"filter": "Folder", "value": "my_movie"}
        ]
        nav_filters._criteria_popup.close()

    def test_apply_filters_logic(self, nav_filters, qtbot):
        """Verify apply_filters_requested calls the filter engine with correct data."""
        nav_filters.settings.settings_data_model.db_enabled.return_value = False

        nav_filters.root_folder = ["/root"]
        mock_items = [MagicMock()]

        # Capture the callback
        captured_callback = None

        def side_effect(path, depth=0, on_complete=None):
            nonlocal captured_callback
            captured_callback = on_complete
            if on_complete:
                on_complete(mock_items)

        nav_filters.file_util.get_files_from_path_async.side_effect = side_effect

        # Set a filter
        nav_filters.filter_table.add_filter("Folder", "my_movie")

        # Mock the final callback
        on_complete_mock = MagicMock()
        with qtbot.waitSignal(nav_filters.loading_started):
            nav_filters.apply_filters(
                selected_folders=["/root/sub"], on_complete=on_complete_mock
            )

        nav_filters.file_util.get_files_from_path_async.assert_called_with(
            "/root/sub", on_complete=captured_callback
        )
        nav_filters.folder_nav_filters_filter.apply_filters.assert_called()
        on_complete_mock.assert_called()

    def test_genre_changed_signal(self, qtbot):
        """Verify genre combo change emits signal in editable mode."""
        table = FolderFilterTable(["Sci-Fi", "Action"], [], readonly=False)
        qtbot.addWidget(table)
        table.add_filter("Genre")
        combo = table.cellWidget(0, 1)
        assert isinstance(combo, QComboBox)
        with qtbot.waitSignal(table.genre_changed) as blocker:
            combo.setCurrentText("Sci-Fi")
        assert blocker.args[0].data == "Sci-Fi"

    def test_media_changed_signal(self, qtbot):
        """Verify media combo change emits root folder signal in editable mode."""
        table = FolderFilterTable(
            [], [{"label": "Movies", "path": "movies"}], readonly=False
        )
        qtbot.addWidget(table)
        table.add_filter("Media")
        combo = table.cellWidget(0, 1)
        assert isinstance(combo, QComboBox)
        with qtbot.waitSignal(table.root_folder) as blocker:
            combo.setCurrentIndex(1)
        assert blocker.args[0].data == "movies"

    def test_load_filter_readonly(self, nav_filters, settings_mock):
        """Verify loading a filter shows readonly text labels and no edit/select widgets."""
        nav_filters.show()
        settings_mock.settings_data_model.saved_filters = [
            {
                "name": "MyFilter",
                "filters": [
                    {"filter": "Folder", "value": "my_movie"},
                    {"filter": "Genre", "value": "Sci-Fi"},
                    {"filter": "Tag", "value": "Favorite"},
                ],
            }
        ]
        nav_filters._refresh_saved_filters_combo()

        # Add temporary tags beforehand
        nav_filters.add_selected_tag("TempTag1")
        nav_filters.add_selected_tag("TempTag2")
        assert len(nav_filters.selected_tags) == 2
        assert nav_filters.selected_tags_container.isVisible()

        index = nav_filters.saved_filters_combo.findText("MyFilter")
        nav_filters.saved_filters_combo.setCurrentIndex(index)

        # Temporary tags should be cleared upon choosing/loading a filter
        assert len(nav_filters.selected_tags) == 0
        assert not nav_filters.selected_tags_container.isVisible()

        assert nav_filters.filter_table.rowCount() == 3
        assert nav_filters.filter_table.columnCount() == 2

        # Verify rows widgets for filter and value
        assert isinstance(nav_filters.filter_table.cellWidget(0, 0), QLabel)
        assert isinstance(nav_filters.filter_table.cellWidget(0, 1), QLabel)
        assert isinstance(nav_filters.filter_table.cellWidget(1, 0), QLabel)
        assert isinstance(nav_filters.filter_table.cellWidget(1, 1), QLabel)
        assert isinstance(nav_filters.filter_table.cellWidget(2, 0), QLabel)
        tag_cloud_widget = nav_filters.filter_table.cellWidget(2, 1)
        assert isinstance(tag_cloud_widget, FilterTagCloudWidget)

        assert nav_filters.filter_table.cellWidget(0, 0).text().strip() == "Folder"
        assert nav_filters.filter_table.cellWidget(0, 1).text().strip() == "my_movie"
        assert nav_filters.filter_table.cellWidget(1, 0).text().strip() == "Genre"
        assert nav_filters.filter_table.cellWidget(1, 1).text().strip() == "Sci-Fi"
        assert nav_filters.filter_table.cellWidget(2, 0).text().strip() == "Tag"
        assert tag_cloud_widget.get_tags() == ["Favorite"]
        assert nav_filters.filter_table.horizontalHeader().minimumSectionSize() >= 90
        assert nav_filters.filter_table.columnWidth(0) >= 90

        # Applying filters should pass all 3 loaded filter criteria to filter engine
        nav_filters._apply_filters_internal([])
        applied_filters = nav_filters.folder_nav_filters_filter.apply_filters.call_args[
            1
        ]["filters"]
        assert len(applied_filters) == 3
        assert {"filter": "Folder", "value": "my_movie"} in applied_filters
        assert {"filter": "Genre", "value": "Sci-Fi"} in applied_filters
        assert {"filter": "Tag", "value": "Favorite"} in applied_filters

    def test_clear_saved_filter_resets_selection_and_criteria(
        self, nav_filters, settings_mock
    ):
        settings_mock.settings_data_model.saved_filters = [
            {
                "name": "MyFilter",
                "filters": [{"filter": "Folder", "value": "my_movie"}],
            }
        ]
        nav_filters._refresh_saved_filters_combo()
        selection_changes = []
        nav_filters.saved_filter_selection_changed.connect(selection_changes.append)

        index = nav_filters.saved_filters_combo.findText("MyFilter")
        nav_filters.saved_filters_combo.setCurrentIndex(index)
        assert selection_changes[-1] is True
        assert nav_filters.filter_table.collect_filters() == [
            {"filter": "Folder", "value": "my_movie"}
        ]

        nav_filters.clear_saved_filter()

        assert nav_filters.saved_filters_combo.currentIndex() == 0
        assert selection_changes[-1] is False
        assert nav_filters.filter_table.collect_filters() == []

    def test_tag_button_opens_popup_without_create(self, nav_filters):
        """Verify tag button popup does not have tag creation controls and does not have trashcan delete buttons."""
        nav_filters._show_tag_cloud()
        assert nav_filters._popup is not None
        assert nav_filters._popup.new_tag_edit is None
        assert nav_filters._popup.create_button is None
        assert nav_filters._popup.allow_create is False
        assert nav_filters._popup.allow_delete is False
        nav_filters._popup.close()

    def test_settings_filters_tab_tag_selection_and_counts(self, qtbot):
        """Verify tag selection in Settings -> Filters shows correct count and color."""
        state = MagicMock(spec=SettingsState)
        state.media_configs = []
        state.saved_filters = [
            {
                "name": "Action Only",
                "filters": [{"filter": "Tag", "value": "Action"}],
            }
        ]
        log = MagicMock()
        tag_store = MagicMock()
        tag_store.list_tags.return_value = [
            {"tag": "Action", "color": "#e74c3c"},
            {"tag": "Drama", "color": "#3498db"},
        ]
        tag_store.get_tag_counts.return_value = {"action": 12, "drama": 5}

        tab = SettingsFilterTab(state, log, tag_store=tag_store)
        qtbot.addWidget(tab)

        assert len(tab.row_widgets) == 1
        filter_table = tab.row_widgets[0].filter_table
        assert filter_table is not None
        assert filter_table.rowCount() == 1

        cloud_widget = filter_table.cellWidget(0, 1)
        assert isinstance(cloud_widget, FilterTagCloudWidget)
        assert cloud_widget.get_tags() == ["Action"]

        btn = cloud_widget._layout.itemAt(0)
        assert btn is not None
        btn_widget = btn.widget()
        assert isinstance(btn_widget, TagButton)
        assert btn_widget.text() == "Action (12)  ✕"
        assert "#e74c3c" in btn_widget.styleSheet()

        # Check collecting filters retrieves raw tag value without qty suffix
        filters = filter_table.collect_filters()
        assert filters == [{"filter": "Tag", "value": "Action"}]

    def test_settings_filters_tab_multi_tag_inline_cloud(self, qtbot):
        """Verify multiple tags append to a single inline tag cloud criteria row."""
        state = MagicMock(spec=SettingsState)
        state.media_configs = []
        state.saved_filters = [
            {
                "name": "Multi Tag Filter",
                "filters": [
                    {"filter": "Tag", "value": "Action"},
                    {"filter": "Tag", "value": "Drama"},
                ],
            }
        ]
        log = MagicMock()
        tag_store = MagicMock()
        tag_store.list_tags.return_value = [
            {"tag": "Action", "color": "#e74c3c"},
            {"tag": "Drama", "color": "#3498db"},
            {"tag": "Sci-Fi", "color": "#2ecc71"},
        ]
        tag_store.get_tag_counts.return_value = {"action": 10, "drama": 4, "sci-fi": 8}

        tab = SettingsFilterTab(state, log, tag_store=tag_store)
        qtbot.addWidget(tab)

        filter_table = tab.row_widgets[0].filter_table
        assert filter_table is not None
        assert filter_table.rowCount() == 1  # Only 1 row for all tags!

        cloud_widget = filter_table.cellWidget(0, 1)
        assert isinstance(cloud_widget, FilterTagCloudWidget)
        assert cloud_widget.get_tags() == ["Action", "Drama"]

        # Add third tag
        cloud_widget.add_tag("Sci-Fi")
        assert cloud_widget.get_tags() == ["Action", "Drama", "Sci-Fi"]

        # Collect filters
        filters = filter_table.collect_filters()
        assert len(filters) == 1
        assert filters[0]["filter"] == "Tag"
        assert filters[0]["value"] == "Action, Drama, Sci-Fi"

        # Remove drama
        cloud_widget.remove_tag("Drama")
        assert cloud_widget.get_tags() == ["Action", "Sci-Fi"]
        filters = filter_table.collect_filters()
        assert filters == [{"filter": "Tag", "value": "Action, Sci-Fi"}]

    def test_multi_tag_row_auto_expands_height(self, qtbot):
        """Verify adding multiple tags to a Tag filter row auto-expands the row height and table height."""
        table = FolderFilterTable(
            genres=["Sci-Fi", "Action"],
            media_configs=[],
            readonly=False,
        )
        qtbot.addWidget(table)
        table.resize(300, 200)
        table.setColumnWidth(0, 95)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 35)

        # Add single tag
        table.add_filter("Tag", "Action")
        single_row_height = table.rowHeight(0)
        single_table_height = table.height()

        cloud_widget = table.cellWidget(0, 1)
        assert isinstance(cloud_widget, FilterTagCloudWidget)

        # Add multiple tags to force multi-line wrapping
        many_tags = [
            "Drama",
            "Comedy",
            "Thriller",
            "Adventure",
            "Documentary",
            "Animation",
            "Sci-Fi",
        ]
        for tag in many_tags:
            cloud_widget.add_tag(tag)

        multi_row_height = table.rowHeight(0)
        multi_table_height = table.height()

        assert multi_row_height > single_row_height
        assert multi_table_height > single_table_height

        # Removing tags should shrink height back
        for tag in many_tags:
            cloud_widget.remove_tag(tag)

        shrunk_row_height = table.rowHeight(0)
        assert shrunk_row_height < multi_row_height

    def test_readonly_multi_tag_row_auto_expands_height(self, qtbot):
        """Verify readonly multi-tag filter table in nav auto-expands row height."""
        table = FolderFilterTable(
            genres=["Sci-Fi", "Action"],
            media_configs=[],
            readonly=True,
        )
        qtbot.addWidget(table)
        table.resize(280, 200)
        table.setColumnWidth(0, 95)
        table.setColumnWidth(1, 150)

        # Add single tag filter
        table.add_filter("Tag", "Action")
        single_h = table.rowHeight(0)

        # Clear and add multiple tags
        table.setRowCount(0)
        table.add_filter(
            "Tag",
            "Action, Drama, Comedy, Thriller, Adventure, Documentary, Animation, Sci-Fi",
        )
        multi_h = table.rowHeight(0)

        assert multi_h > single_h

    def test_settings_tab_add_extra_tags_expands_height(self, qtbot):
        """Verify adding extra tags dynamically in settings tab expands the table and row height."""
        state = MagicMock(spec=SettingsState)
        state.media_configs = []
        state.saved_filters = [
            {
                "name": "My Filter",
                "filters": [
                    {"filter": "Tag", "value": "Action"},
                ],
            }
        ]
        log = MagicMock()
        tag_store = MagicMock()
        tag_store.list_tags.return_value = [
            {"tag": f"Tag{i}", "color": "#e74c3c"} for i in range(20)
        ]
        tag_store.get_tag_counts.return_value = {f"tag{i}": i for i in range(20)}

        tab = SettingsFilterTab(state, log, tag_store=tag_store)
        tab.resize(500, 600)
        tab.show()
        qtbot.addWidget(tab)
        qtbot.waitExposed(tab)

        table = tab.row_widgets[0].filter_table
        assert table is not None
        cloud_widget = table.cellWidget(0, 1)
        assert isinstance(cloud_widget, FilterTagCloudWidget)

        initial_row_height = table.rowHeight(0)
        initial_table_height = table.height()

        # Add 10 tags
        for i in range(10):
            cloud_widget.add_tag(f"LongTagNumber{i}")

        after_row_height = table.rowHeight(0)
        after_table_height = table.height()

        assert after_row_height > initial_row_height
        assert after_table_height > initial_table_height

    def test_stretch_column_resizing(self, qtbot):
        """Verify resizing the table recomputes row heights when columns stretch."""
        table = FolderFilterTable(
            genres=["Sci-Fi", "Action"],
            media_configs=[],
            readonly=True,
        )
        table.show()
        qtbot.addWidget(table)
        qtbot.waitExposed(table)

        table.add_filter(
            "Tag",
            "Action, Drama, Comedy, Thriller, Adventure, Documentary, Animation, Sci-Fi",
        )
        table.resize(200, 300)
        narrow_h = table.rowHeight(0)

        table.resize(600, 300)
        wide_h = table.rowHeight(0)

        assert narrow_h > wide_h

    def test_tag_item_text_is_hidden_underneath_cloud(self, qtbot):
        """Verify that QTableWidgetItem text is empty so it does not render under the tag cloud."""
        table = FolderFilterTable(
            genres=["Sci-Fi", "Action"],
            media_configs=[],
            readonly=False,
        )
        qtbot.addWidget(table)
        table.add_filter("Tag", "Action, Sci-Fi")

        item = table.item(0, 1)
        assert item is not None
        assert item.text() == ""
        assert item.data(Qt.ItemDataRole.UserRole) == "Action, Sci-Fi"

        # Dynamically add another tag
        cloud = table.cellWidget(0, 1)
        assert isinstance(cloud, FilterTagCloudWidget)
        cloud.add_tag("Drama")
        assert item.text() == ""
        assert item.data(Qt.ItemDataRole.UserRole) == "Action, Sci-Fi, Drama"

        # Verify readonly mode also hides underlying item text
        ro_table = FolderFilterTable(
            genres=["Sci-Fi", "Action"],
            media_configs=[],
            readonly=True,
        )
        qtbot.addWidget(ro_table)
        ro_table.add_filter("Tag", "Action, Sci-Fi")
        ro_item = ro_table.item(0, 1)
        assert ro_item is not None
        assert ro_item.text() == ""
        assert ro_item.data(Qt.ItemDataRole.UserRole) == "Action, Sci-Fi"

    def test_add_tag_button_remains_at_end_and_does_not_overlap_first_tag(self, qtbot):
        """Verify Add Tag button remains at the end of the inline cloud and matches tag height."""
        table = FolderFilterTable(
            genres=["Sci-Fi", "Action"],
            media_configs=[],
            readonly=False,
        )
        table.show()
        qtbot.addWidget(table)
        qtbot.waitExposed(table)
        table.resize(400, 200)

        table.add_filter("Tag", "Action")
        cloud = table.cellWidget(0, 1)
        assert isinstance(cloud, FilterTagCloudWidget)

        # Get tag button and add button
        buttons = cloud.findChildren(QToolButton)
        assert len(buttons) == 2  # 1 tag pill + 1 add button
        tag_btn = buttons[0]
        add_btn = buttons[1]

        def is_after(w1, w2) -> bool:
            # Returns True if w2 is placed after w1 in flow layout reading order
            r1 = w1.geometry()
            r2 = w2.geometry()
            return r2.y() > r1.y() or (r2.y() == r1.y() and r2.x() >= r1.right())

        # Verify add button is positioned after the first tag, not at (0, 0) overlapping it
        assert is_after(tag_btn, add_btn)
        # Verify height is compact and does not exceed tag pill height
        assert add_btn.sizeHint().height() <= tag_btn.sizeHint().height()

        # Add more tags dynamically
        cloud.add_tag("Comedy")
        buttons = cloud.findChildren(QToolButton)
        assert len(buttons) == 3
        first_tag_btn = buttons[0]
        second_tag_btn = buttons[1]
        add_btn = buttons[2]

        assert is_after(first_tag_btn, second_tag_btn)
        assert is_after(second_tag_btn, add_btn)

        # Remove a tag dynamically
        cloud.remove_tag("Action")
        buttons = cloud.findChildren(QToolButton)
        assert len(buttons) == 2
        remaining_tag_btn = buttons[0]
        add_btn = buttons[1]

        assert is_after(remaining_tag_btn, add_btn)
