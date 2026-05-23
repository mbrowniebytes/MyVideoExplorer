import pytest
from unittest.mock import patch
from src.settings.settings_state import SettingsState
import json


class TestSettingsSplit:
    @pytest.fixture(autouse=True)
    def setup_cfg(self, tmp_path, monkeypatch):
        # Create a temporary cfg directory
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()

        # Patch CFG_DIR and file paths in SettingsState
        monkeypatch.setattr("src.settings.settings_state.CFG_DIR", cfg_dir)
        monkeypatch.setattr(
            "src.settings.settings_state.SETTINGS_UI_FILE", cfg_dir / "settings_ui.json"
        )
        monkeypatch.setattr(
            "src.settings.settings_state.SETTINGS_MEDIA_FILE",
            cfg_dir / "settings_media.json",
        )
        monkeypatch.setattr(
            "src.settings.settings_state.SETTINGS_FILTER_FILE",
            cfg_dir / "settings_filter.json",
        )
        monkeypatch.setattr(
            "src.settings.settings_state.DEFAULTS_UI_FILE", cfg_dir / "defaults_ui.json"
        )
        monkeypatch.setattr(
            "src.settings.settings_state.DEFAULTS_MEDIA_FILE",
            cfg_dir / "defaults_media.json",
        )
        monkeypatch.setattr(
            "src.settings.settings_state.DEFAULTS_FILTER_FILE",
            cfg_dir / "defaults_filter.json",
        )

        return cfg_dir

    def test_ensure_defaults_creates_split_files(self, setup_cfg):
        cfg_dir = setup_cfg
        state = SettingsState()
        state._ensure_defaults()

        assert (cfg_dir / "defaults_ui.json").exists()
        assert (cfg_dir / "defaults_media.json").exists()
        assert (cfg_dir / "defaults_filter.json").exists()

        # Verify content
        with open(cfg_dir / "defaults_ui.json") as f:
            ui_data = json.load(f)
            assert "font_size" in ui_data

    def test_save_settings_creates_split_files(self, setup_cfg):
        cfg_dir = setup_cfg
        state = SettingsState()
        state.folder_configs = [{"label": "Test", "path": "/test", "icon": "folder"}]
        state.save_settings()

        assert (cfg_dir / "settings_ui.json").exists()
        assert (cfg_dir / "settings_media.json").exists()
        assert (cfg_dir / "settings_filter.json").exists()

        with open(cfg_dir / "settings_media.json") as f:
            media_data = json.load(f)
            assert media_data["folder_configs"][0]["label"] == "Test"

    def test_load_settings_merges_split_files(self, setup_cfg):
        cfg_dir = setup_cfg

        # Pre-create settings files
        (cfg_dir / "settings_ui.json").write_text(
            json.dumps({"font_size": 22}), encoding="utf-8"
        )
        (cfg_dir / "settings_media.json").write_text(
            json.dumps({"folder_configs": [{"label": "Loaded", "path": "/loaded"}]}),
            encoding="utf-8",
        )

        state = SettingsState()
        # _load_settings is called in __init__

        from src.theme.theme import APP_THEME

        assert APP_THEME.font_size == 22
        assert state.folder_configs[0]["label"] == "Loaded"
        # Check if icon was added by migration/ensure logic
        assert state.folder_configs[0]["icon"] == "folder"

    def test_backups_for_each_file(self, setup_cfg):
        state = SettingsState()

        # Create initial settings
        state.save_settings()

        # Mock date to ensure backup is created if it was already created today (though test runs once)
        # Actually backup_file only creates one per day.
        # To test it creates backups for each, we just check if they are called.

        with patch("src.utils.json_util.JsonUtil.backup_file") as mock_backup:
            state.save_settings()
            # Should be called 4 times, once for each settings file (app, ui, media, filter)
            assert mock_backup.call_count == 4

            # Verify paths - check that all settings files are in the called paths
            called_paths = [str(call.args[0]) for call in mock_backup.call_args_list]
            assert any("settings_app.json" in path for path in called_paths)
            assert any("settings_ui.json" in path for path in called_paths)
            assert any("settings_media.json" in path for path in called_paths)
            assert any("settings_filter.json" in path for path in called_paths)

    def test_delete_filter_logic(self, setup_cfg):
        state = SettingsState()
        state.saved_filters = [
            {"name": "Filter1", "filters": []},
            {"name": "Filter2", "filters": []},
        ]

        state.delete_filter("Filter1")
        assert len(state.saved_filters) == 1
        assert state.saved_filters[0]["name"] == "Filter2"

        # Verify it was saved
        with open(setup_cfg / "settings_filter.json") as f:
            data = json.load(f)
            assert len(data["saved_filters"]) == 1
