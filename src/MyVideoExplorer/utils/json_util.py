import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from MyVideoExplorer.utils.log_util import LogUtil


class JsonUtil:
    """Utility class for JSON file operations with backup management."""

    DEFAULT_ENCODING = "utf-8"
    DEFAULT_INDENT = 4
    MAX_BACKUPS_DEFAULT = 5
    CFG_DIR = Path("cfg")

    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util

    def ensure_defaults(
        self, cfg_dir: Path, defaults_file: Path, default_data: dict[str, Any]
    ) -> None:
        """Create config directory and default JSON file if they don't exist."""
        cfg_dir.mkdir(parents=True, exist_ok=True)

        if not defaults_file.exists():
            self.save_json(defaults_file, default_data)

    def load_json(self, file_path: Path) -> dict[str, Any]:
        """Load JSON data from a file. Returns empty dict on error or missing file."""
        try:
            with open(file_path, encoding=self.DEFAULT_ENCODING) as f:
                data: Any = json.load(f)
                return data
        except (OSError, json.JSONDecodeError) as e:
            self.log_util.error(f"Failed to load {file_path}: {e}")
            return {}

    def save_json(self, file_path: Path, data: dict[str, Any]) -> None:
        """Save data to a JSON file with proper error handling."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding=self.DEFAULT_ENCODING) as f:
                json.dump(data, f, indent=self.DEFAULT_INDENT)
        except OSError as e:
            self.log_util.error(f"Failed to save {file_path}: {e}")

    def backup_file(self, file_path: Path, max_backups: int = MAX_BACKUPS_DEFAULT) -> None:
        """Manage daily backups of a file, keeping up to max_backups."""
        if not file_path.exists():
            return


        if "PYTEST_CURRENT_TEST" in os.environ:
            cfg_dir = file_path.parent
        else:
            # explict set
            cfg_dir = self.CFG_DIR

        today_str = datetime.now().strftime("%Y-%m-%d")
        backup_name = cfg_dir / f"{file_path.stem}_{today_str}{file_path.suffix}"

        # Only create one backup per day
        if not backup_name.exists():
            try:
                shutil.copy2(file_path, backup_name)
            except OSError as e:
                self.log_util.error(f"Failed to backup {file_path}: {e}")
                return

        # Keep only the max_backups most recent backups
        pattern = f"{file_path.stem}_*{file_path.suffix}"
        # explicit check, since deleting files
        if pattern.find("settings_") == -1:
            self.log_util.warn(f"Failed to delete old backups with unexpected pattern {pattern}")
            return

        backups = sorted(cfg_dir.glob(pattern), reverse=True, key=os.path.getmtime)

        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except OSError as e:
                self.log_util.warn(f"Failed to delete old backup {old_backup}: {e}")
