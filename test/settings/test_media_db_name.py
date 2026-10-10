from unittest.mock import MagicMock, patch

from MyVideoExplorer.db.db_scan_worker import ScanWorker
from MyVideoExplorer.settings.settings_media_folder_browser_section import (
    SettingsMediaFolderBrowserSection,
)
from MyVideoExplorer.settings.settings_state import SettingsState


def test_settings_state_get_db_path():
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util)
            assert state.get_db_path({"label": "Movies"}) == "db/media_Movies.db"
            assert state.get_db_path({"label": ""}) == "db/media_media.db"
            assert (
                state.get_db_path({"label": "TV Shows"}, "Anime")
                == "db/media_Anime.db"
            )
            assert state.get_db_path({"label": ".."}) == "db/media_media.db"


def test_scan_worker_get_db_path():
    mock_file_util = MagicMock()
    mock_nfo_util = MagicMock()

    worker = ScanWorker(
        {"label": "Documentaries", "path": "/path"}, mock_file_util, mock_nfo_util
    )
    assert worker._get_db_path() == "db/media_Documentaries.db"

    worker_empty = ScanWorker(
        {"label": "", "path": "/path"}, mock_file_util, mock_nfo_util
    )
    assert worker_empty._get_db_path() == "db/media_media.db"

    worker_special = ScanWorker(
        {"label": "Sci-Fi / Fantasy", "path": "/path"},
        mock_file_util,
        mock_nfo_util,
    )
    assert worker_special._get_db_path() == "db/media_Sci-Fi _ Fantasy.db"


def test_rename_db_for_media_config(tmp_path, monkeypatch):
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util)

            # Change working directory or mock get_db_path to tmp_path
            db_dir = tmp_path / "db"
            db_dir.mkdir()
            old_file = db_dir / "media_OldName.db"
            old_file.write_text("db content")

            monkeypatch.chdir(tmp_path)

            config = {
                "label": "NewName",
                "_previous_label": "OldName",
                "path": "/path",
            }
            state.rename_db_for_media_config(config)

            assert not old_file.exists()
            new_file = db_dir / "media_NewName.db"
            assert new_file.exists()
            assert new_file.read_text() == "db content"
            assert config["_previous_label"] == "NewName"


def test_section_rename_db_file_if_needed(tmp_path, monkeypatch, qtbot):
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    old_file = db_dir / "media_OldSection.db"
    old_file.write_text("section db content")

    monkeypatch.chdir(tmp_path)

    mock_file_util = MagicMock()
    mock_nfo_util = MagicMock()

    config = {
        "label": "NewSection",
        "_previous_label": "OldSection",
        "path": "/path",
    }

    section = SettingsMediaFolderBrowserSection(
        media_config=config,
        get_db_path_callback=lambda c, label_override=None: f"db/media_{c.get('label')}.db",
        file_util=mock_file_util,
        nfo_util=mock_nfo_util,
        parent=None,
    )
    qtbot.addWidget(section)

    section._rename_db_file_if_needed(config)

    assert not old_file.exists()
    new_file = db_dir / "media_NewSection.db"
    assert new_file.exists()
    assert new_file.read_text() == "section db content"
    assert config["_previous_label"] == "NewSection"
