import pytest
from unittest.mock import MagicMock
from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class TestFolderNavFilters:
    @pytest.fixture
    def settings_mock(self):
        settings = MagicMock()
        settings.settings_data_model.folder_configs = [
            {"label": "Movies", "path": "movies"},
            {"label": "TV Shows", "path": "tv"},
        ]
        settings.saved_filters = []
        return settings

    @pytest.fixture
    def nav_filters(self, qtbot, settings_mock):
        file_util = MagicMock(spec=FileUtil)
        nfo_util = MagicMock(spec=NfoParseUtil)
        engine = FolderFilterFilter(nfo_util)
        engine.apply_filters = MagicMock(side_effect=engine.apply_filters)
        mock_log = MagicMock()
        widget = FolderFilters(engine, file_util, settings_mock, mock_log)
        widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_ui_initialization(self, nav_filters):
        """Verify that UI components are correctly initialized."""
        assert nav_filters.apply_button.toolTip().strip() == "Apply Filters"
        # Starts with 1 row (placeholder)
        assert nav_filters.filter_table.rowCount() == 1
        assert (
            nav_filters.filter_table.item(0, 0).text()
            == "Add a Filter from above dropdown"
        )

        # filter_type_combo count should be length of FILTER_TYPES
        # plus any separators
        expected_count = len(nav_filters.filter_table.FILTER_TYPES)
        for filter_type in nav_filters.filter_table.FILTER_TYPES:
            if filter_type.casefold() in ("os", "nfo", "media"):
                expected_count += 1

        assert nav_filters.filter_type_combo.count() == expected_count

    def test_add_remove_filter(self, nav_filters):
        """Verify adding and removing filters."""
        # Find "Folder" in combo
        index = nav_filters.filter_type_combo.findText("  Folder")
        if index == -1:
            index = nav_filters.filter_type_combo.findText("Folder")
        nav_filters.filter_type_combo.setCurrentIndex(index)

        nav_filters.add_filter_button.click()
        assert nav_filters.filter_table.rowCount() == 1
        assert nav_filters.filter_table.item(0, 0).text().strip() == "Folder"

        # Remove it
        remove_btn = nav_filters.filter_table.cellWidget(0, 2)
        remove_btn.click()
        # Back to 1 row (placeholder)
        assert nav_filters.filter_table.rowCount() == 1
        assert (
            nav_filters.filter_table.item(0, 0).text()
            == "Add a Filter from above dropdown"
        )

    def test_collect_filters(self, nav_filters):
        """Verify that filters are correctly collected from the table."""
        # Add Folder filter
        nav_filters.filter_table.add_filter("Folder", "test_folder")

        # Add File filter
        nav_filters.filter_table.add_filter("File", "*.mp4")

        filters = nav_filters.filter_table.collect_filters()

        folder_filter = next((f for f in filters if f["filter"] == "Folder"), None)
        assert folder_filter is not None
        assert folder_filter["value"] == "test_folder"

        file_filter = next((f for f in filters if f["filter"] == "File"), None)
        assert file_filter is not None
        assert file_filter["value"] == "*.mp4"

    def test_apply_filters_trigger(self, nav_filters, qtbot):
        """Verify that clicking apply button emits signal."""
        with qtbot.waitSignal(nav_filters.sig_apply_filters) as blocker:
            nav_filters.apply_button.click()
        assert blocker.args is not None

    def test_apply_filters_logic(self, nav_filters, qtbot):
        """Verify apply_filters calls the filter engine with correct data."""
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
        with qtbot.waitSignal(nav_filters.sig_loading_started):
            nav_filters.apply_filters(selected_folders=["/root/sub"], on_complete=on_complete_mock)

        nav_filters.file_util.get_files_from_path_async.assert_called_with("/root/sub", on_complete=captured_callback)
        nav_filters.folder_nav_filters_filter.apply_filters.assert_called()

        # Check if callback was called
        on_complete_mock.assert_called()

    def test_genre_changed_signal(self, nav_filters, qtbot):
        """Verify genre combo change emits signal."""
        nav_filters.filter_table.add_filter("Genre")
        combo = nav_filters.filter_table.cellWidget(0, 1)
        with qtbot.waitSignal(nav_filters.sig_genre_changed) as blocker:
            combo.setCurrentText("Sci-Fi")
        assert blocker.args[0].data == "Sci-Fi"

    def test_media_changed_signal(self, nav_filters, qtbot):
        """Verify media combo change emits root folder signal."""
        nav_filters.filter_table.add_filter("Media")
        combo = nav_filters.filter_table.cellWidget(0, 1)
        with qtbot.waitSignal(nav_filters.sig_root_folder) as blocker:
            # Index 0 is "- Select Folder -", 1 is "Movies"
            combo.setCurrentIndex(1)
        assert blocker.args[0].data == "movies"

    def test_save_filter(self, nav_filters, settings_mock, qtbot):
        """Verify saving a filter."""
        nav_filters.filter_table.add_filter("Folder", "my_movie")
        filters = [{"filter": "Folder", "value": "my_movie"}]

        # Set text in editable combo
        nav_filters.saved_filters_combo.setEditText("MyFilter")

        nav_filters.save_filter_button.click()

        settings_mock.save_filter.assert_called_with("MyFilter", filters)

    def test_load_filter(self, nav_filters, settings_mock):
        """Verify loading a filter."""
        settings_mock.settings_data_model.saved_filters = [
            {"name": "MyFilter", "filters": [{"filter": "Folder", "value": "my_movie"}]}
        ]
        nav_filters._refresh_saved_filters_combo()

        index = nav_filters.saved_filters_combo.findText("MyFilter")
        nav_filters.saved_filters_combo.setCurrentIndex(index)

        nav_filters._load_saved_filter(index)

        assert nav_filters.filter_table.rowCount() == 1
        assert nav_filters.filter_table.item(0, 0).text().strip() == "Folder"
        assert nav_filters.filter_table.item(0, 1).text().strip() == "my_movie"
