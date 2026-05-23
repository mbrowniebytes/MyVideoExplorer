import json
import shutil
from datetime import datetime
from pathlib import Path


class JsonUtil:
    def __init__(self, log_util=None):
        self.log_util = log_util

    def ensure_defaults(self, cfg_dir: Path, defaults_file: Path, default_data: dict):
        """Create cfg directory and defaults_[section].json if they don't exist."""
        if not cfg_dir.exists():
            cfg_dir.mkdir(parents=True)

        if not defaults_file.exists():
            with open(defaults_file, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)

    def load_json(self, file_path: Path) -> dict:
        """Load JSON data from a file."""
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"Warning: Failed to load {file_path}: {e}")
        return {}

    def save_json(self, file_path: Path, data: dict):
        """Save data to a JSON file."""
        cfg_dir = file_path.parent
        if not cfg_dir.exists():
            cfg_dir.mkdir(parents=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def backup_file(self, file_path: Path, max_backups: int = 5):
        """Manage daily backups of a file, keeping up to max_backups."""
        if not file_path.exists():
            return

        cfg_dir = file_path.parent
        today_str = datetime.now().strftime("%Y-%m-%d")
        backup_name = cfg_dir / f"{file_path.stem}_{today_str}{file_path.suffix}"

        # Only create one backup per day
        if not backup_name.exists():
            shutil.copy2(file_path, backup_name)

        # Keep only the max_backups most recent backups
        backups = sorted(
            cfg_dir.glob(f"{file_path.stem}_*{file_path.suffix}"), reverse=True
        )
        if len(backups) > max_backups:
            for old_backup in backups[max_backups:]:
                old_backup.unlink()
