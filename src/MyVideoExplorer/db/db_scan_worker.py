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
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_type import FileUtilType
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class ScanWorker(QThread):
    finished = Signal()
    progress_init = Signal(int)
    progress_updated = Signal(int)

    def __init__(self, media_config: dict[str, Any], file_util: FileUtil, nfo_util: NfoParseUtil):
        super().__init__()
        self.media_config = media_config
        self.file_util = file_util
        self.nfo_util = nfo_util

    def _backup_db(self, db_path: str):
        if not os.path.exists(db_path):
            return

        db_path_obj = Path(db_path)

        # backup path: db/[media]_[YYYY-MM-DD].db
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        backup_name = f"{db_path_obj.stem}_{today_str}{db_path_obj.suffix}"
        backup_path = db_path_obj.parent / backup_name

        # Only create one backup per day
        if not backup_path.exists():
            try:
                shutil.copy2(db_path, backup_path)
            except OSError:
                return

        # Keep 5 most recent backups
        backup_pattern = f"{db_path_obj.stem}_*{db_path_obj.suffix}"
        backups = sorted(db_path_obj.parent.glob(backup_pattern), reverse=True, key=os.path.getmtime)

        max_backups = 5
        for old_backup in backups[max_backups:]:
            try:
                old_backup.unlink()
            except OSError:
                pass

    def run(self):
        # Scan folder
        new_results = []
        media_path = self.media_config.get("path", "")

        # Count all folders for progress bar
        total_folders = 0
        if os.path.isdir(media_path):
            for _, dirs, _ in os.walk(media_path):
                total_folders += 1
        self.progress_init.emit(total_folders)

        stats = {
            'media_path': media_path,
            'subfolders_count': 0,
            'files_count': 0,
            'images_count': 0,
            'videos_count': 0,
            'nfo_count': 0,
            'other_count': 0,
            'last_scanned': datetime.datetime.now()
        }

        progress = 0
        if media_path and os.path.isdir(media_path):
            for root, dirs, files in os.walk(media_path):
                stats['subfolders_count'] += len(dirs)
                stats['files_count'] += len(files)

                # Update progress for each directory visited
                progress += 1
                self.progress_updated.emit(progress)

                for file in files:
                    # dev test large qty folders
                    if IS_DEVELOPMENT:
                        sleep(0.011)

                    ext = os.path.splitext(file)[1].lower()
                    if ext in FileUtilType.VIDEO_EXTS:
                        stats['videos_count'] += 1
                        file_path = os.path.join(root, file).replace(os.path.sep, '/')

                        # Find NFO in the same directory as the video
                        nfo_path = self.file_util.find_nfo_in_list(root, files)
                        metadata = None
                        if nfo_path:
                            metadata = self.nfo_util.parse_nfo_file(nfo_path)
                        new_results.append(
                            {"file_path": file_path, "metadata": metadata}
                        )
                    elif ext in FileUtilType.NFO_EXTS:
                        stats['nfo_count'] += 1
                    elif ext in FileUtilType.IMAGE_EXTS:
                        stats['images_count'] += 1
                    else:
                        stats['other_count'] += 1

        # Save to DB
        db_path = self._get_db_path()
        # TODO inject log_util
        if db_path == "":
            print(f"no db path from label name: {self.media_config.get("label", "")}")
            return

        self._backup_db(db_path)

        db_util = DbScanUtil(db_path)
        db_util.save_media(new_results, media_path)
        db_util.save_stats(stats)

        self.finished.emit()

    def _get_db_path(self):
        label = self.media_config.get("label", "")
        if label == "":
            return ""
        safe_label = re.sub(r'[^a-zA-Z0-9_\-.]', '_', label)
        if safe_label == "":
            return ""
        return os.path.join("db", f"{safe_label}.db")
