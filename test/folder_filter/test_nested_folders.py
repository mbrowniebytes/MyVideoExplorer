import pytest
from unittest.mock import MagicMock, patch
from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
import os

class TestNestedFolderStructure:
    @pytest.fixture
    def settings_mock(self):
        settings = MagicMock()
        settings.settings_data_model.folder_configs = [
            {"label": "Movies", "path": "movies"},
        ]
        settings.settings_data_model.db_enabled.return_value = True

        os.makedirs("db", exist_ok=True)
        db_path = "db/Movies.db"
        with open(db_path, "w") as f:
            f.write("dummy")

        settings.settings_data_model.get_db_path.return_value = db_path

        settings.saved_filters = []
        return settings

    @pytest.fixture
    def nav_filters(self, qtbot, settings_mock):
        file_util = MagicMock(spec=FileUtil)
        # Mock build_hierarchy_from_paths
        def build_hierarchy_mock(paths, folder_path):
            models = []
            for p in ["movies", "movies/subdir1", "movies/subdir1/movie1.mp4", "movies/subdir1/movie2.mp4"]:
                m = MagicMock(spec=FileUtilModel)
                m.full_path = p
                m.is_dir = p in ["movies", "movies/subdir1"]
                m.is_file = not m.is_dir
                models.append(m)
            return models
        file_util.build_hierarchy_from_paths = build_hierarchy_mock

        nfo_util = MagicMock(spec=NfoParseUtil)
        engine = FolderFilterFilter(nfo_util, settings_mock.settings_data_model)

        mock_log = MagicMock()
        widget = FolderFilters(engine, file_util, settings_mock, mock_log)
        widget.root_folders = ["movies"]
        widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_nested_folders_added(self, nav_filters, qtbot):
        with patch("duckdb.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            # Mock the query result with nested subfolders
            mock_con.execute.return_value.fetchall.return_value = [
                ("movies/subdir1/movie1.mp4",),
                ("movies/subdir1/movie2.mp4",)
            ]

            # Add a filter
            nav_filters.filter_table.add_filter("File", "movie")

            on_complete_mock = MagicMock()

            # Bypass filtering for verification
            with patch.object(nav_filters, "_apply_filters_internal", side_effect=lambda x: x):
                nav_filters.apply_filters(selected_folders=["movies"], on_complete=on_complete_mock)

            # Verify that items were added.
            # We expect 'movies', 'movies/subdir1', 'movie1.mp4', 'movie2.mp4' (or similar)
            # Actually, the file scan logic adds dirs.

            items = on_complete_mock.call_args[0][0]

            # The expected structure is nested folders, so we should see 'movies' and 'subdir1' as dirs.

            paths = [item.full_path for item in items]

            # Print paths for debugging
            print(f"Paths: {paths}")

            assert "movies" in paths
            assert "movies/subdir1" in paths
            assert "movies/subdir1/movie1.mp4" in paths
            assert "movies/subdir1/movie2.mp4" in paths
