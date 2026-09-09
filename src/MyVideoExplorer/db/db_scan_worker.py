import os
import re
import datetime
import shutil
from pathlib import Path
from time import sleep
from typing import Any

from PySide6.QtCore import QThread, Signal

from MyVideoExplorer.app.app_environment import IS_DEVELOPMENT
from MyVideoExplorer.db.db_scan import DbScanUtil
from MyVideoExplorer.lang.lang_loader import LangLoader
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_type import FileUtilType
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class ScanWorker(QThread):
    finished = Signal()
    error = Signal(str)
    progress_init = Signal(int)
    progress_updated = Signal(int)
    progress_stage = Signal(str)

    def __init__(
        self, media_config: dict[str, Any], file_util: FileUtil, nfo_util: NfoParseUtil
    ):
        super().__init__()
        self.media_config = media_config
        self.file_util = file_util
        self.nfo_util = nfo_util
        self.lang = LangLoader.get_lang("en")

    @staticmethod
    def _format_error(exc: BaseException) -> str:
        details = str(exc).strip()
        if not details:
            return "The scan could not be saved to the database."
        cleaned = details.replace("\n", " ")
        if "permission" in cleaned.lower():
            return (
                "The scan could not be saved because the database file is not writable. "
                f"Please check folder permissions. Details: {cleaned}"
            )
        if "no such file" in cleaned.lower() or "not found" in cleaned.lower():
            return (
                "The selected media folder could not be found or is no longer available. "
                f"Details: {cleaned}"
            )
        return (
            "The scan could not be saved to the database. "
            f"Please check the media name, folder path, and database permissions. Details: {cleaned}"
        )

    def _backup_db(self, db_path: str):
        if not Path(db_path).exists():
            return

        db_path_obj = Path(db_path)
        backup_dir = db_path_obj.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # backup path: db/backups/[media]_[YYYY-MM-DD].db
        today_str = (
            datetime.datetime.now(datetime.UTC).astimezone().strftime("%Y-%m-%d")
        )
        backup_name = f"{db_path_obj.stem}_{today_str}{db_path_obj.suffix}"
        backup_path = backup_dir / backup_name

        # Only create one backup per day
        if not backup_path.exists():
            try:
                shutil.copy2(db_path, backup_path)
            except OSError:
                return

        # Keep 5 most recent backups
        backup_pattern = f"{db_path_obj.stem}_*{db_path_obj.suffix}"
        backups = sorted(
            backup_dir.glob(backup_pattern),
            reverse=True,
            key=lambda p: p.stat().st_mtime,
        )

        max_backups = 5
        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except OSError:
                pass

    def run(self):
        try:
            # Scan folder
            new_results = []
            media_path = self.media_config.get("path", "")

            # Count all folders for progress bar
            total_folders = 0
            media_path_obj = Path(media_path)
            if media_path_obj.is_dir():
                for _ in media_path_obj.rglob("*"):
                    if _.is_dir():
                        total_folders += 1
            self.progress_init.emit(100)
            self.progress_stage.emit(
                self.lang.scan_progress["scanning_media_subfolders"]
            )

            stats = {
                "media_path": media_path,
                "subfolders_count": 0,
                "files_count": 0,
                "images_count": 0,
                "videos_count": 0,
                "nfo_count": 0,
                "other_count": 0,
                "last_scanned": datetime.datetime.now(datetime.UTC),
            }

            progress = 0
            if media_path and Path(media_path).is_dir():
                folder_steps = max(total_folders, 1)
                for root, dirs, files in os.walk(media_path):
                    stats["subfolders_count"] += len(dirs)
                    stats["files_count"] += len(files)

                    # Update scan progress until 75% then transition to DB save.
                    progress += 1
                    scan_progress = min(75, int((progress / folder_steps) * 75))
                    self.progress_updated.emit(scan_progress)

                    for file in files:
                        # dev test large qty folders
                        if IS_DEVELOPMENT:
                            sleep(0.011)

                        file_path_obj = Path(root) / file
                        ext = file_path_obj.suffix.lower()
                        if ext in FileUtilType.VIDEO_EXTS:
                            stats["videos_count"] += 1
                            file_path = file_path_obj.as_posix()

                            # Find NFO in the same directory as the video
                            nfo_path = self.file_util.find_nfo_in_list(root, files)
                            metadata = None
                            if nfo_path:
                                metadata = self.nfo_util.parse_nfo_file(nfo_path)
                            new_results.append(
                                {"file_path": file_path, "metadata": metadata}
                            )
                        elif ext in FileUtilType.NFO_EXTS:
                            stats["nfo_count"] += 1
                        elif ext in FileUtilType.IMAGE_EXTS:
                            stats["images_count"] += 1
                        else:
                            stats["other_count"] += 1

            # Save to DB
            db_path = self._get_db_path()
            if db_path == "":
                raise ValueError(
                    "The media name is empty or contains no valid characters for database storage."
                )
            if not media_path or not Path(media_path).is_dir():
                raise FileNotFoundError(f"Media folder not found: {media_path}")

            self.progress_stage.emit(self.lang.scan_progress["saving_media_data"])
            self.progress_updated.emit(75)
            self._backup_db(db_path)

            def on_db_progress(pct: int, label: str):
                self.progress_stage.emit(label)
                self.progress_updated.emit(
                    min(100, max(75, int(75 + (pct / 100) * 25)))
                )

            db_util = DbScanUtil(db_path)
            db_util.save_media(
                new_results,
                media_path,
                progress_callback=lambda pct, label: on_db_progress(pct, label),
            )
            db_util.save_stats(stats, progress_callback=on_db_progress)
            self.progress_updated.emit(100)
        except Exception as exc:  # pragma: no cover - surfaced via UI dialog
            self.error.emit(self._format_error(exc))
        finally:
            self.finished.emit()

    def _get_db_path(self):
        label = str(self.media_config.get("label", "")).strip()
        if label == "":
            return ""
        safe_label = re.sub(r"[^a-zA-Z0-9_\-]", "_", label)
        if safe_label.strip("._-") == "":
            return ""
        # Return path using POSIX separator so DB filenames use '/' even on Windows
        return f"db/{safe_label}.db"
