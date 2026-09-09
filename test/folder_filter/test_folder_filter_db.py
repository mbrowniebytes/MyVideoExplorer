from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil

class TestFolderNavFiltersDB:
    @pytest.fixture
    def settings_mock(self):
        settings = MagicMock()
        # Mock media_configs with absolute paths or paths that will match
        settings.settings_data_model.media_configs = [
            {"label": "Movies", "path": "movies"},
        ]
        settings.settings_data_model.db_enabled.return_value = True

        # Mock get_db_path to return a path that exists
        # We'll create a dummy db file
        db_path = Path("tmp/db/Test.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text("dummy", encoding="utf-8")

        settings.settings_data_model.get_db_path.return_value = db_path

        settings.saved_filters = []
        return settings

    @pytest.fixture
    def nav_filters(self, qtbot, settings_mock):
        file_util = MagicMock(spec=FileUtil)
        # Mock build_hierarchy_from_paths
        mock_dir = MagicMock(spec=FileUtilModel)
        mock_dir.is_dir = True
        mock_dir.is_file = False
        mock_dir.full_path = "movies"
        mock_dir.name = "movies"

        mock_file = MagicMock(spec=FileUtilModel)
        mock_file.is_dir = False
        mock_file.is_file = True
        mock_file.full_path = "movies/movie1.mp4"
        mock_file.name = "movie1.mp4"

        file_util.build_hierarchy_from_paths.return_value = [mock_dir, mock_file]

        nfo_util = MagicMock(spec=NfoParseUtil)
        # We need to ensure FolderFilterFilter also uses the updated db_enabled status
        engine = FolderFilterFilter(nfo_util, settings_mock.settings_data_model)

        mock_log = MagicMock()
        widget = FolderFilters(engine, file_util, settings_mock, mock_log)
        widget.root_folders = ["movies"] # Matches config path
        widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_apply_filters_db_enabled(self, nav_filters, qtbot):
        # We need to mock duckdb
        with patch("duckdb.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            # Mock the query result
            mock_con.execute.return_value.fetchall.return_value = [("movies/movie1.mp4",)]

            # Add a filter to ensure we get results back
            nav_filters.filter_table.add_filter("File", "movie1")

            on_complete_mock = MagicMock()

            nav_filters.apply_filters(selected_folders=["movies"], on_complete=on_complete_mock)

            # Verify that duckdb was called
            mock_connect.assert_called_with("tmp/db/Test.db")

            # Verify that items were added
            assert on_complete_mock.called
            items = on_complete_mock.call_args[0][0]
            # We expect a dir
            assert len(items) == 1
            assert items[0].is_dir
            assert items[0].full_path == "movies"
