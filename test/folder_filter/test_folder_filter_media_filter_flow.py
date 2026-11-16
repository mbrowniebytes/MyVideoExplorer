from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.lang.lang_en import LangEn
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.utils.file_util import FileUtil


@pytest.fixture
def filter_db_path(tmp_path):
    """Provide an isolated filter database path to avoid file lock conflicts."""
    return tmp_path / "filter_catalog.db"


def test_media_filter_selection_should_emit_filters_requested(
    qtbot, filter_db_path: Path
):
    """Verify that checking a media folder in the combo triggers filters_requested."""
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util, filter_db_path=filter_db_path)
            state.media_configs = [
                {"label": "Movies", "path": "/movies"},
                {"label": "TV", "path": "/tv"},
            ]
            state.selected_media_folders = []

            settings = MagicMock()
            settings.settings_data_model = state

            file_util = MagicMock(spec=FileUtil)
            nfo_util = MagicMock()
            engine = FolderFilterFilter(nfo_util, state)
            widget = FolderFilters(engine, file_util, settings, mock_log_util, LangEn())
            widget.build()
            qtbot.addWidget(widget)

            # Initially no filters
            filters = widget.collect_media_filters()
            assert filters == []

            # Check the "Movies" action
            action = widget.media_filter_combo._actions.get("Movies")
            assert action is not None

            filter_requested_count = 0

            def count_filters():
                nonlocal filter_requested_count
                filter_requested_count += 1

            widget.filters_requested.connect(count_filters)

            # Toggle the Movies checkbox via the action
            with qtbot.waitSignal(widget.media_filter_combo.selection_changed):
                action.setChecked(True)
                widget.media_filter_combo._on_triggered(action)

            # Should have collected the Movies filter
            filters = widget.collect_media_filters()
            assert len(filters) == 1
            assert filters[0]["filter"] == "media"
            assert "/movies" in filters[0]["value"]

            # filters_requested should have been emitted
            assert filter_requested_count >= 1


def test_media_filter_select_none_should_show_all(qtbot, filter_db_path: Path):
    """Verify that unchecking all media folders clears the filter."""
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util, filter_db_path=filter_db_path)
            state.media_configs = [
                {"label": "Movies", "path": "/movies"},
                {"label": "TV", "path": "/tv"},
            ]
            state.selected_media_folders = []

            settings = MagicMock()
            settings.settings_data_model = state

            file_util = MagicMock(spec=FileUtil)
            nfo_util = MagicMock()
            engine = FolderFilterFilter(nfo_util, state)
            widget = FolderFilters(engine, file_util, settings, mock_log_util, LangEn())
            widget.build()
            qtbot.addWidget(widget)

            # Check Movies
            movies_action = widget.media_filter_combo._actions.get("Movies")
            assert movies_action is not None
            movies_action.setChecked(True)
            widget.media_filter_combo._on_triggered(movies_action)

            filters = widget.collect_media_filters()
            assert len(filters) == 1

            # Uncheck Movies
            movies_action.setChecked(False)
            widget.media_filter_combo._on_triggered(movies_action)

            filters = widget.collect_media_filters()
            assert filters == []


def test_media_filter_select_all_should_show_all(qtbot, filter_db_path: Path):
    """Verify that selecting all media folders still filters by those folders."""
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util, filter_db_path=filter_db_path)
            state.media_configs = [
                {"label": "Movies", "path": "/movies"},
                {"label": "TV", "path": "/tv"},
            ]
            state.selected_media_folders = []

            settings = MagicMock()
            settings.settings_data_model = state

            file_util = MagicMock(spec=FileUtil)
            nfo_util = MagicMock()
            engine = FolderFilterFilter(nfo_util, state)
            widget = FolderFilters(engine, file_util, settings, mock_log_util, LangEn())
            widget.build()
            qtbot.addWidget(widget)

            # Check all
            widget.media_filter_combo.select_all()

            filters = widget.collect_media_filters()
            assert len(filters) == 2
            paths = []
            for f in filters:
                paths.extend(f["value"])
            assert "/movies" in paths
            assert "/tv" in paths
