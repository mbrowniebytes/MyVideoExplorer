import json
from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.settings.settings_state import SettingsState


class TestSettingsSplit:
    @pytest.fixture
    def mock_log_util(self):
        return MagicMock()

    @pytest.fixture(autouse=True)
    def setup_cfg(self, tmp_path, monkeypatch):
        # Create a temporary cfg directory
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()

        # Patch CFG_DIR and file paths in SettingsState
        monkeypatch.setattr("MyVideoExplorer.settings.settings_state.CFG_DIR", cfg_dir)
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.SETTINGS_APP_FILE",
            cfg_dir / "settings_app.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.SETTINGS_UI_FILE",
            cfg_dir / "settings_ui.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.SETTINGS_MEDIA_FILE",
            cfg_dir / "settings_media.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.SETTINGS_FILTER_FILE",
            cfg_dir / "settings_filter.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.DEFAULT_FILTER_DB_PATH",
            cfg_dir / "filter_catalog.db",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.DEFAULTS_APP_FILE",
            cfg_dir / "defaults_app.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.DEFAULTS_UI_FILE",
            cfg_dir / "defaults_ui.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.DEFAULTS_MEDIA_FILE",
            cfg_dir / "defaults_media.json",
        )
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_state.DEFAULTS_FILTER_FILE",
            cfg_dir / "defaults_filter.json",
        )

        return cfg_dir

    def test_ensure_defaults_creates_split_files(self, setup_cfg, mock_log_util):
        cfg_dir = setup_cfg
        state = SettingsState(mock_log_util)
        state._ensure_defaults()

        assert (cfg_dir / "defaults_ui.json").exists()
        assert (cfg_dir / "defaults_media.json").exists()
        assert (cfg_dir / "defaults_filter.json").exists()
        assert (cfg_dir / "defaults_app.json").exists()
        assert (cfg_dir / "settings_app.json").exists()

        # Verify content
        with (cfg_dir / "defaults_ui.json").open(encoding="utf-8") as f:
            ui_data = json.load(f)
            assert "font_size" in ui_data

        with (cfg_dir / "settings_app.json").open(encoding="utf-8") as f:
            app_data = json.load(f)
            assert "log_level" in app_data

    def test_save_settings_creates_split_files(self, setup_cfg, mock_log_util):
        cfg_dir = setup_cfg
        state = SettingsState(mock_log_util)
        state.media_configs = [{"label": "Test", "path": "/test", "icon": "folder"}]
        state.save_settings()

        assert (cfg_dir / "settings_ui.json").exists()
        assert (cfg_dir / "settings_media.json").exists()
        assert not (cfg_dir / "settings_filter.json").exists()

        with (cfg_dir / "settings_media.json").open(encoding="utf-8") as f:
            media_data = json.load(f)
            assert media_data["media_configs"][0]["label"] == "Test"

        state.scan_media_timeout_seconds = 300
        state.save_app()
        with (cfg_dir / "settings_app.json").open(encoding="utf-8") as f:
            app_data = json.load(f)
        assert app_data["scan_media_timeout_seconds"] == 300

    def test_load_settings_merges_split_files(self, setup_cfg, mock_log_util):
        cfg_dir = setup_cfg

        # Pre-create settings files
        (cfg_dir / "settings_ui.json").write_text(
            json.dumps({"font_size": 22}), encoding="utf-8"
        )
        (cfg_dir / "settings_media.json").write_text(
            json.dumps({"media_configs": [{"label": "Loaded", "path": "/loaded"}]}),
            encoding="utf-8",
        )

        state = SettingsState(mock_log_util)
        # _load_settings is called in __init__

        from MyVideoExplorer.theme.theme import APP_THEME

        assert APP_THEME.font_size == 22
        assert state.media_configs[0]["label"] == "Loaded"
        # Check if icon was added by migration/ensure logic
        assert state.media_configs[0]["icon"] == "fa6s.folder"

    def test_legacy_filter_json_should_migrate_once_to_database(
        self, setup_cfg, mock_log_util
    ):
        legacy = [
            {"name": "Custom", "filters": [{"filter": "title", "value": "alpha"}]}
        ]
        (setup_cfg / "settings_filter.json").write_text(
            json.dumps({"saved_filters": legacy}), encoding="utf-8"
        )

        state = SettingsState(mock_log_util)
        assert state.saved_filters[0]["name"] == "Custom"
        assert state.filter_store.list_filters()[0]["filters"] == legacy[0]["filters"]

        state.save_filter("Updated", [], original_name="Custom")
        reloaded = SettingsState(mock_log_util)

        assert [item["name"] for item in reloaded.saved_filters] == ["Updated"]
        with (setup_cfg / "settings_filter.json").open(encoding="utf-8") as file:
            assert json.load(file)["saved_filters"] == legacy

    def test_backups_for_each_file(self, setup_cfg, mock_log_util):
        state = SettingsState(mock_log_util)

        # Create initial settings
        state.save_settings()

        # Mock date to ensure backup is created if it was already created today (though test runs once)
        # Actually backup_file only creates one per day.
        # To test it creates backups for each, we just check if they are called.

        with patch(
            "MyVideoExplorer.utils.json_util.JsonUtil.backup_file"
        ) as mock_backup:
            state.save_settings()
            # Filters are persisted in the filter catalog database.
            assert mock_backup.call_count == 3

            # Verify paths - check that all settings files are in the called paths
            called_paths = [str(call.args[0]) for call in mock_backup.call_args_list]
            assert any("settings_app.json" in path for path in called_paths)
            assert any("settings_ui.json" in path for path in called_paths)
            assert any("settings_media.json" in path for path in called_paths)

    def test_delete_filter_logic(self, setup_cfg, mock_log_util):
        state = SettingsState(mock_log_util)
        state.saved_filters = [
            {"name": "Filter1", "filters": []},
            {"name": "Filter2", "filters": []},
        ]
        state.save_filters()

        state.delete_filter("Filter1")
        assert len(state.saved_filters) == 1
        assert state.saved_filters[0]["name"] == "Filter2"
        assert [item["name"] for item in state.filter_store.list_filters()] == [
            "Filter2"
        ]

    def test_save_filter_with_original_name_should_rename_in_place(
        self, setup_cfg, mock_log_util
    ):
        state = SettingsState(mock_log_util)
        state.saved_filters = [
            {"name": "A", "filters": []},
            {"name": "B", "filters": []},
            {"name": "C", "filters": []},
        ]
        state.save_filters()
        new_cfg = [{"filter": "Folder", "value": "x"}]

        state.save_filter("B2", new_cfg, original_name="B")

        assert [f["name"] for f in state.saved_filters] == ["A", "B2", "C"]
        assert state.saved_filters[1]["filters"] == new_cfg

    def test_save_filter_rename_onto_existing_name_should_not_duplicate(
        self, setup_cfg, mock_log_util
    ):
        state = SettingsState(mock_log_util)
        state.saved_filters = [
            {"name": "A", "filters": []},
            {"name": "B", "filters": []},
        ]
        state.save_filters()

        state.save_filter("A", [], original_name="B")

        assert [f["name"] for f in state.saved_filters] == ["A"]

    def test_save_filter_should_emit_settings_changed_once(
        self, setup_cfg, mock_log_util
    ):
        state = SettingsState(mock_log_util)
        received: list[object] = []
        state.settings_changed.connect(received.append)

        state.save_filter("New", [])
        assert len(received) == 1

        state.delete_filter("New")
        assert len(received) == 2

    def test_load_scan_timeout_setting_and_default(self, setup_cfg, mock_log_util):
        settings_app = setup_cfg / "settings_app.json"
        settings_app.write_text(
            json.dumps({"scan_media_timeout_seconds": 60}), encoding="utf-8"
        )
        assert SettingsState(mock_log_util).scan_media_timeout_seconds == 60

        settings_app.write_text(
            json.dumps({"scan_media_timeout_seconds": 45}), encoding="utf-8"
        )
        assert SettingsState(mock_log_util).scan_media_timeout_seconds == 120
