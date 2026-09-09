import json
import os
import shutil
import datetime
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
            with file_path.open(encoding=self.DEFAULT_ENCODING) as f:
                data: Any = json.load(f)
                return data
        except (OSError, json.JSONDecodeError) as e:
            self.log_util.error(f"Failed to load {file_path}: {e}")
            return {}

    def save_json(self, file_path: Path, data: dict[str, Any]) -> None:
        """Atomically write JSON to avoid partially-written settings files."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = file_path.parent / f".{file_path.name}.{os.getpid()}.tmp"
            with temp_path.open("w", encoding=self.DEFAULT_ENCODING) as f:
                json.dump(data, f, indent=self.DEFAULT_INDENT)
                f.flush()
                os.fsync(f.fileno())
            temp_path.replace(file_path)
        except OSError as e:
            self.log_util.error(f"Failed to save {file_path}: {e}")
        finally:
            temp_path = file_path.parent / f".{file_path.name}.{os.getpid()}.tmp"
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def backup_file(self, file_path: Path, max_backups: int = MAX_BACKUPS_DEFAULT) -> None:
        """Manage daily backups of a file, keeping up to max_backups."""
        if not file_path.exists():
            return

        backup_dir = file_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_pattern = f"{file_path.stem}_*{file_path.suffix}"

        try:
            current_contents = file_path.read_text(encoding=self.DEFAULT_ENCODING)
        except OSError as e:
            self.log_util.error(f"Failed to read {file_path}: {e}")
            return

        # Only backup if the content has changed since the latest backup.
        backups = sorted(
            backup_dir.glob(backup_pattern), reverse=True, key=lambda p: p.stat().st_mtime
        )
        if backups:
            latest_backup = backups[0]
            try:
                if latest_backup.read_text(encoding=self.DEFAULT_ENCODING) == current_contents:
                    return
            except OSError:
                pass

        today_str = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
        backup_name = backup_dir / f"{file_path.stem}_{today_str}{file_path.suffix}"

        # Only create one backup per day
        if not backup_name.exists():
            try:
                shutil.copy2(file_path, backup_name)
            except OSError as e:
                self.log_util.error(f"Failed to backup {file_path}: {e}")
                return

        # Keep only the max_backups most recent backups
        backups = sorted(
            backup_dir.glob(backup_pattern), reverse=True, key=lambda p: p.stat().st_mtime
        )

        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except OSError as e:
                self.log_util.warning(f"Failed to delete old backup {old_backup}: {e}")
