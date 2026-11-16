from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import duckdb
from PySide6.QtCore import QThread, Signal

from MyVideoExplorer.db import db_query
from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.ffprobe_util import FfprobeUtil
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_type import FileUtilType

logger = logging.getLogger(__name__)


class FfprobeWorker(QThread):
    """Background thread that runs ffprobe on video files sequentially."""

    finished = Signal()
    error = Signal(str)
    progress_init = Signal(int)  # total files to scan
    progress_updated = Signal(int, str)  # current file index (1-based), file name
    progress_stage = Signal(str)  # stage label

    def __init__(
        self,
        ffmpeg_folder: str,
        media_config: dict[str, Any],
        scan_new_only: bool,
        file_util: FileUtil,
    ) -> None:
        super().__init__()
        self.ffmpeg_folder = ffmpeg_folder
        self.media_config = media_config
        self.scan_new_only = scan_new_only
        self.file_util = file_util

    def _get_db_path(self) -> str:
        """Compute the media database path from the config label."""
        label = str(self.media_config.get("label", "")).strip()
        if not label:
            label = "media"
        safe_label = re.sub(r"[^a-zA-Z0-9_.\-\s]", "_", label)
        safe_label = re.sub(r"\s+", " ", safe_label).strip()
        safe_label = safe_label.strip(" ._-")
        if safe_label in {"", ".", ".."}:
            safe_label = "media"
        return f"db/media_{safe_label}.db"

    def run(self) -> None:
        try:
            db_path = self._get_db_path()

            # Ensure migrations are applied
            DbMigrations(db_path).run_migrations()

            # Query all video files from media_file table
            video_exts = list(FileUtilType.VIDEO_EXTS)
            files_to_scan: list[tuple[int, str]] = []

            with duckdb.connect(db_path) as con:
                rows = con.execute(
                    db_query.DbQuery.MediaFile.SELECT_VIDEO_FILES,
                    (video_exts,),
                ).fetchall()
                files_to_scan = [(row[0], row[1]) for row in rows]

            if not files_to_scan:
                self.progress_init.emit(0)
                self.progress_stage.emit("No video files found")
                self.finished.emit()
                return

            # Filter by scan mode
            if self.scan_new_only:
                ff_util = FfprobeUtil(self.ffmpeg_folder, db_path)
                scanned_ids = ff_util.get_scanned_file_ids()
                files_to_scan = [
                    (fid, fpath)
                    for fid, fpath in files_to_scan
                    if fid not in scanned_ids
                ]
                if not files_to_scan:
                    self.progress_init.emit(0)
                    self.progress_stage.emit("All files already scanned")
                    self.finished.emit()
                    return

            total = len(files_to_scan)
            self.progress_init.emit(total)
            self.progress_stage.emit("Probing video files with ffprobe…")

            ff_util = FfprobeUtil(self.ffmpeg_folder, db_path)

            for i, (file_id, file_path) in enumerate(files_to_scan, start=1):
                if self.isInterruptionRequested():
                    logger.info("ffprobe scan cancelled at file %d/%d", i, total)
                    self.progress_stage.emit("Scan cancelled")
                    return

                file_name = Path(file_path).name
                self.progress_updated.emit(i, file_name)

                # Check file still exists
                if not Path(file_path).is_file():
                    logger.warning("File not found, skipping: %s", file_path)
                    continue

                probe_data = ff_util.probe_file(file_path)
                if probe_data is None:
                    logger.warning("ffprobe returned no data for: %s", file_path)
                    continue

                try:
                    ff_util.save_probe_result(file_id, probe_data)
                except Exception as exc:
                    logger.error(
                        "Failed to save probe result for %s: %s", file_path, exc
                    )
                    self.error.emit(f"Failed to save metadata for {file_name}: {exc}")

            self.progress_stage.emit("Scan complete")
            self.progress_updated.emit(total, "Done")

        except Exception as exc:
            logger.exception("ffprobe worker failed")
            self.error.emit(f"ffprobe scan failed: {exc}")
        finally:
            self.finished.emit()
