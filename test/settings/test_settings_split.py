import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QCheckBox, QLineEdit, QRadioButton

from MyVideoExplorer.settings.settings_player_tab import SettingsPlayerTab
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
            "MyVideoExplorer.settings.settings_state.SETTINGS_PLAYER_FILE",
            cfg_dir / "settings_player.json",
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
            "MyVideoExplorer.settings.settings_state.DEFAULTS_PLAYER_FILE",
            cfg_dir / "defaults_player.json",
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
        assert (cfg_dir / "defaults_player.json").exists()

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
        assert (cfg_dir / "settings_player.json").exists()
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
            assert mock_backup.call_count == 4

            # Verify paths - check that all settings files are in the called paths
            called_paths = [str(call.args[0]) for call in mock_backup.call_args_list]
            assert any("settings_app.json" in path for path in called_paths)
            assert any("settings_player.json" in path for path in called_paths)
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

    def test_save_filter_rename_onto_existing_name_should_raise_error(
        self, setup_cfg, mock_log_util
    ):
        state = SettingsState(mock_log_util)
        state.saved_filters = [
            {"name": "A", "filters": []},
            {"name": "B", "filters": []},
        ]
        state.save_filters()

        with pytest.raises(ValueError, match="already exists"):
            state.save_filter("A", [], original_name="B")

        # Filters should remain unchanged
        assert [f["name"] for f in state.saved_filters] == ["A", "B"]

    def test_save_filter_rename_case_insensitive_onto_existing_should_raise(
        self, setup_cfg, mock_log_util
    ):
        state = SettingsState(mock_log_util)
        state.saved_filters = [
            {"name": "Alpha", "filters": []},
            {"name": "Beta", "filters": []},
        ]
        state.save_filters()

        with pytest.raises(ValueError, match="already exists"):
            state.save_filter("alpha", [], original_name="Beta")

        assert [f["name"] for f in state.saved_filters] == ["Alpha", "Beta"]

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

    def test_video_player_settings_round_trip(self, setup_cfg, mock_log_util):
        state = SettingsState(mock_log_util)
        vlc = next(
            player for player in state.video_player_configs if player["id"] == "vlc"
        )
        vlc["executable"] = "C:/Apps/VLC/vlc.exe"
        vlc["show_icon"] = True
        vlc["is_default"] = True
        state.video_player_configs[0]["is_default"] = False
        custom = next(
            player for player in state.video_player_configs if player["id"] == "custom"
        )
        custom["arguments"] = '--fullscreen --profile "My Profile"'
        state.save_player()

        reloaded = SettingsState(mock_log_util)
        saved_vlc = next(
            player for player in reloaded.video_player_configs if player["id"] == "vlc"
        )
        assert saved_vlc["executable"] == "C:/Apps/VLC/vlc.exe"
        assert saved_vlc["show_icon"] is True
        assert saved_vlc["is_default"] is True
        saved_custom = next(
            player
            for player in reloaded.video_player_configs
            if player["id"] == "custom"
        )
        assert saved_custom["arguments"] == '--fullscreen --profile "My Profile"'
        os_default = reloaded.video_player_configs[0]
        assert os_default["id"] == "os_default"
        assert os_default["is_default"] is False
        assert [player["id"] for player in reloaded.video_player_configs] == [
            "os_default",
            "vlc",
            "potplayer",
            "mpc_qt",
            "custom",
        ]

    def test_video_tab_locks_os_default_player(self, setup_cfg, mock_log_util, qtbot):
        state = SettingsState(mock_log_util)
        tab = SettingsPlayerTab(state, mock_log_util)
        qtbot.addWidget(tab)

        radios = tab.findChildren(QRadioButton)
        assert len(radios) == 5
        assert sum(radio.isChecked() for radio in radios) == 1
        assert radios[0].isChecked()
        assert all(radio.isEnabled() for radio in radios)
        os_default_show = tab.findChild(QCheckBox, "os_default_show_checkbox")
        assert os_default_show is not None
        assert not os_default_show.isEnabled()
        assert os_default_show.isChecked()
        assert "disabled" in os_default_show.styleSheet()
        argument_edits = tab.findChildren(QLineEdit)
        player_arguments = [
            edit for edit in argument_edits if edit.objectName().endswith("_arguments")
        ]
        assert len(player_arguments) == 5
        assert all(edit.text() == "" for edit in player_arguments)
        custom_label = next(
            player["label"]
            for player in state.video_player_configs
            if player["id"] == "custom"
        )
        assert custom_label == "Custom"
        vlc_radio = next(
            radio for radio in radios if radio.toolTip().startswith("Use VLC")
        )
        vlc_radio.click()
        assert sum(radio.isChecked() for radio in radios) == 1
        assert vlc_radio.isChecked()
        assert next(
            player for player in state.video_player_configs if player["id"] == "vlc"
        )["is_default"]

    def test_video_player_defaults_include_common_windows_paths(
        self, setup_cfg, mock_log_util
    ):
        state = SettingsState(mock_log_util)
        executables = {
            player["id"]: player["executable"] for player in state.video_player_configs
        }
        assert executables["vlc"] == "C:/Program Files/VideoLAN/VLC/vlc.exe"
        assert (
            executables["potplayer"]
            == "C:/Program Files/DAUM/PotPlayer/PotPlayerMini64.exe"
        )
        assert executables["mpc_qt"] == "C:/Program Files/MPC-QT/mpc-qt.exe"

    def test_legacy_player_settings_are_migrated(self, setup_cfg, mock_log_util):
        legacy_players = [
            {
                "id": "vlc",
                "executable": "C:/Legacy/vlc.exe",
                "show_icon": True,
                "is_default": True,
            }
        ]
        (setup_cfg / "settings_app.json").write_text(
            json.dumps({"video_player_configs": legacy_players}), encoding="utf-8"
        )

        state = SettingsState(mock_log_util)

        vlc = next(
            player for player in state.video_player_configs if player["id"] == "vlc"
        )
        assert vlc["executable"] == "C:/Legacy/vlc.exe"
        assert vlc["show_icon"] is True
        assert vlc["is_default"] is True
