from unittest.mock import MagicMock

import pytest
import json
from MyVideoExplorer.utils.json_util import JsonUtil

class TestJsonUtil:
    @pytest.fixture
    def mock_log_util(self):
        return MagicMock()


    @pytest.fixture
    def json_util(self, mock_log_util):
        return JsonUtil(log_util=mock_log_util)


    def test_ensure_defaults(self, tmp_path, json_util):
        cfg_dir = tmp_path / "cfg"
        defaults_file = cfg_dir / "defaults_ui.json"
        default_data = {"font_size": 18}

        json_util.ensure_defaults(cfg_dir, defaults_file, default_data)

        assert cfg_dir.exists()
        assert defaults_file.exists()
        with open(defaults_file) as f:
            data = json.load(f)
        assert data == default_data


    def test_load_json(self, tmp_path, json_util):
        file_path = tmp_path / "test.json"
        test_data = {"a": 1}
        with open(file_path, "w") as f:
            json.dump(test_data, f)

        loaded_data = json_util.load_json(file_path)
        assert loaded_data == test_data


    def test_load_json_non_existent(self, tmp_path, json_util):
        file_path = tmp_path / "non_existent.json"
        loaded_data = json_util.load_json(file_path)
        assert loaded_data == {}


    def test_save_json(self, tmp_path, json_util):
        file_path = tmp_path / "subdir" / "test.json"
        test_data = {"b": 2}

        json_util.save_json(file_path, test_data)

        assert file_path.exists()
        with open(file_path) as f:
            data = json.load(f)
        assert data == test_data


    def test_backup_file(self, tmp_path, json_util):
        file_path = tmp_path / "settings_ui.json"
        file_path.write_text("content")

        json_util.backup_file(file_path, max_backups=2)

        backups = list(tmp_path.glob("settings_ui_*.json"))
        assert len(backups) == 1
        assert backups[0].read_text() == "content"


    def test_backup_file_rotation(self, tmp_path, json_util):
        file_path = tmp_path / "settings_ui.json"
        file_path.write_text("content")

        # Create manual old backups
        (tmp_path / "settings_ui_2026-04-01.json").write_text("old1")
        (tmp_path / "settings_ui_2026-04-02.json").write_text("old2")
        (tmp_path / "settings_ui_2026-04-03.json").write_text("old3")

        json_util.backup_file(file_path, max_backups=2)

        backups = sorted(tmp_path.glob("settings_ui_*.json"), reverse=True)
        # Today's backup + 1 old backup (rotation should keep most recent by name)
        assert len(backups) == 2
