from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class TestNestedFolderStructure:
    @pytest.fixture
    def settings_mock(self):
        settings = MagicMock()
        settings.settings_data_model.media_configs = [
            {"label": "Movies", "path": "movies"},
        ]
        settings.settings_data_model.db_enabled.return_value = True

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
        def build_hierarchy_mock(paths, folder_path):
            models = []
            for p in [
                "movies",
                "movies/subdir1",
                "movies/subdir1/movie1.mp4",
                "movies/subdir1/movie2.mp4",
            ]:
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

    def test_database_filter_returns_matching_nested_parent_folder(
        self, nav_filters, qtbot
    ):
        with patch("duckdb.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            # Mock the query result with nested subfolders
            mock_con.execute.return_value.fetchall.return_value = [
                ("movies/subdir1/movie1.mp4",),
                ("movies/subdir1/movie2.mp4",),
            ]

            # Add a filter
            nav_filters.filter_table.add_filter("File", "movie")

            on_complete_mock = MagicMock()

            nav_filters.apply_filters(
                selected_folders=["movies"], on_complete=on_complete_mock
            )

            items = on_complete_mock.call_args[0][0]
            assert [item.full_path for item in items] == ["movies/subdir1"]
