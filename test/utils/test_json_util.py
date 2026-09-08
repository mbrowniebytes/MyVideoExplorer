import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from datetime import datetime, timedelta
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

    def test_save_json_uses_atomic_replace(self, tmp_path, json_util, monkeypatch):
        file_path = tmp_path / "settings_ui.json"
        calls = []

        def fake_replace(src, dst):
            calls.append((src, dst))
            Path(dst).write_text(Path(src).read_text(encoding="utf-8"), encoding="utf-8")

        monkeypatch.setattr(os, "replace", fake_replace)

        json_util.save_json(file_path, {"font_size": 21})

        assert len(calls) == 1
        assert Path(calls[0][1]) == file_path
        assert json.loads(file_path.read_text(encoding="utf-8")) == {"font_size": 21}


    def test_backup_file(self, tmp_path, json_util):
        file_path = tmp_path / "settings_ui.json"
        file_path.write_text("content")

        json_util.backup_file(file_path, max_backups=2)

        backups = list((tmp_path / "backups").glob("settings_ui_*.json"))
        assert len(backups) == 1
        assert backups[0].read_text() == "content"


    def test_backup_file_rotation(self, tmp_path, json_util):
        file_path = tmp_path / "settings_ui.json"
        file_path.write_text("content")

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        # Create manual old backups
        (backup_dir / "settings_ui_2026-04-01.json").write_text("old1")
        (backup_dir / "settings_ui_2026-04-02.json").write_text("old2")
        (backup_dir / "settings_ui_2026-04-03.json").write_text("old3")

        json_util.backup_file(file_path, max_backups=2)

        backups = sorted(backup_dir.glob("settings_ui_*.json"), reverse=True)
        # Today's backup + 1 old backup (rotation should keep most recent by name)
        assert len(backups) == 2

    def test_backup_file_no_change(self, tmp_path, json_util, monkeypatch):
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")
        file_path = tmp_path / "settings_ui.json"
        content = "content"
        file_path.write_text(content)

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        # Create a backup with same content (from "yesterday")
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        backup_path = backup_dir / f"settings_ui_{yesterday_str}.json"
        backup_path.write_text(content)

        json_util.backup_file(file_path)

        # Should still have only 1 backup (the old one)
        backups = list(backup_dir.glob("settings_ui_*.json"))
        assert len(backups) == 1
        assert yesterday_str in backups[0].name

    def test_backup_file_with_change(self, tmp_path, json_util, monkeypatch):
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")
        file_path = tmp_path / "settings_ui.json"
        content = "new content"
        file_path.write_text(content)

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        # Create a backup with different content
        (backup_dir / "settings_ui_2026-04-01.json").write_text("old content")

        json_util.backup_file(file_path)

        # Should have 2 backups now
        backups = list(backup_dir.glob("settings_ui_*.json"))
        assert len(backups) == 2

        today_str = datetime.now().strftime("%Y-%m-%d")
        today_backup = backup_dir / f"settings_ui_{today_str}.json"
        assert today_backup.exists()
        assert today_backup.read_text() == content
