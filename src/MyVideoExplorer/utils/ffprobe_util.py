from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.db import db_migrations, db_query
from MyVideoExplorer.db.db_snowflake_id import SnowflakeIdGenerator
from MyVideoExplorer.db.models.ffprobe_stats import FfprobeStats
from MyVideoExplorer.utils.file_util import FileUtils

logger = logging.getLogger(__name__)


class FfprobeUtil:
    """Runs ffprobe on video files and stores stream metadata in DuckDB."""

    def __init__(self, ffmpeg_folder: str, db_path: str) -> None:
        try:
            self.db_path = FileUtils.normalize_path(db_path)
            self.ffprobe_path = self._resolve_ffprobe(ffmpeg_folder)
            self._init_db()
        except Exception:
            logger.exception("Failed to initialize FfprobeUtil for %s", db_path)
            raise

    def _init_db(self) -> None:
        """Ensure the database schema is up to date."""
        try:
            db_migrations.DbMigrations(self.db_path).run_migrations()
        except Exception:
            logger.exception("Failed to run DB migrations for %s", self.db_path)
            raise

    @staticmethod
    def _resolve_ffprobe(folder: str) -> Path:
        """Resolve the ffprobe binary path inside the given folder."""
        base = Path(folder)
        if os.name == "nt":
            return base / "ffprobe.exe"
        return base / "ffprobe"

    def _run_in_transaction(self, operation):
        """Execute *operation* inside a single DuckDB transaction."""
        con = duckdb.connect(self.db_path)
        try:
            con.begin()
            result = operation(con)
            con.commit()
            return result
        except Exception:
            con.rollback()
            logger.exception("DuckDB transaction failed for %s", self.db_path)
            raise
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def probe_file(self, file_path: str) -> dict[str, Any] | None:
        """Run ffprobe on *file_path* and return the parsed JSON output.

        Returns `None` when ffprobe fails or produces no output.
        """
        try:
            result = subprocess.run(
                [
                    str(self.ffprobe_path),
                    "-v",
                    "error",
                    "-print_format",
                    "json",
                    "-show_streams",
                    "-show_format",
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                logger.warning(
                    "ffprobe failed for %s (code %d): %s",
                    file_path,
                    result.returncode,
                    result.stderr.strip(),
                )
                return None
            output = result.stdout.strip()
            if not output:
                return None
            return json.loads(output)
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning("ffprobe error for %s: %s", file_path, exc)
            return None

    def save_probe_result(self, media_file_id: int, probe_data: dict[str, Any]) -> None:
        """Parse ffprobe JSON and upsert video/audio/subtitle rows."""
        try:
            streams = probe_data.get("streams", [])
            fmt = probe_data.get("format", {})
            id_gen = SnowflakeIdGenerator()

            video_rows: list[tuple[Any, ...]] = []
            audio_rows: list[tuple[Any, ...]] = []
            subtitle_rows: list[tuple[Any, ...]] = []

            # Collect audio bitrates first for video bitrate calculation
            audio_bitrates: list[int] = []
            for stream in streams:
                if stream.get("codec_type") == "audio":
                    br = self._safe_int(stream.get("bit_rate"))
                    if br is not None:
                        audio_bitrates.append(br)

            # Get overall format bitrate for video bitrate estimation
            overall_bitrate = self._safe_int(fmt.get("bit_rate"))

            for stream in streams:
                stype = stream.get("codec_type")
                sindex = stream.get("index", 0)
                tags = stream.get("tags") or {}
                disposition = stream.get("disposition") or {}

                if stype == "video":
                    # Determine video bitrate: prefer stream-level, fall back to calculation
                    video_bitrate = self._safe_int(stream.get("bit_rate"))
                    if video_bitrate is None and overall_bitrate is not None:
                        # Calculate: overall_bitrate - sum(audio_bitrates)
                        calculated = overall_bitrate - sum(audio_bitrates)
                        if calculated > 0:
                            video_bitrate = calculated
                    video_rows.append(
                        (
                            id_gen.generate(),
                            media_file_id,
                            sindex,
                            stream.get("width"),
                            stream.get("height"),
                            stream.get("codec_name"),
                            stream.get("codec_long_name"),
                            stream.get("profile"),
                            stream.get("pix_fmt"),
                            stream.get("avg_frame_rate") or stream.get("r_frame_rate"),
                            video_bitrate,
                            self._safe_float(stream.get("duration")),
                            stream.get("color_range"),
                            stream.get("color_space"),
                            stream.get("color_transfer"),
                        )
                    )

                elif stype == "audio":
                    audio_rows.append(
                        (
                            id_gen.generate(),
                            media_file_id,
                            sindex,
                            stream.get("codec_name"),
                            stream.get("profile"),
                            stream.get("channels"),
                            stream.get("channel_layout"),
                            self._safe_int(stream.get("sample_rate")),
                            self._safe_int(stream.get("bit_rate")),
                            tags.get("language"),
                            bool(disposition.get("default", False)),
                            bool(disposition.get("forced", False)),
                        )
                    )

                elif stype == "subtitle":
                    subtitle_rows.append(
                        (
                            id_gen.generate(),
                            media_file_id,
                            sindex,
                            stream.get("codec_name"),
                            tags.get("language"),
                            bool(disposition.get("default", False)),
                            bool(disposition.get("forced", False)),
                            tags.get("title"),
                        )
                    )

            def _upsert(con):
                # Delete old rows for this file first, then insert fresh ones
                con.execute(
                    db_query.DbQuery.FfprobeVideo.DELETE_BY_FILE, (media_file_id,)
                )
                con.execute(
                    db_query.DbQuery.FfprobeAudio.DELETE_BY_FILE, (media_file_id,)
                )
                con.execute(
                    db_query.DbQuery.FfprobeSubtitle.DELETE_BY_FILE, (media_file_id,)
                )

                for row in video_rows:
                    con.execute(db_query.DbQuery.FfprobeVideo.UPSERT, row)
                for row in audio_rows:
                    con.execute(db_query.DbQuery.FfprobeAudio.UPSERT, row)
                for row in subtitle_rows:
                    con.execute(db_query.DbQuery.FfprobeSubtitle.UPSERT, row)

            self._run_in_transaction(_upsert)
        except Exception:
            logger.exception(
                "Failed to save probe result for media_file_id=%d", media_file_id
            )
            raise

    def get_scanned_file_ids(self) -> set[int]:
        """Return media_file_ids that already have video metadata rows."""
        try:
            with duckdb.connect(self.db_path) as con:
                rows = con.execute(
                    db_query.DbQuery.FfprobeVideo.SELECT_SCANNED_IDS
                ).fetchall()
            return {row[0] for row in rows}
        except Exception:
            return set()

    def get_stats(self) -> FfprobeStats:
        """Return scan counts and the latest update from ffprobe metadata tables."""
        try:
            with duckdb.connect(self.db_path) as con:
                row = con.execute(db_query.DbQuery.FfprobeStats.SELECT).fetchone()
            if row is None:
                raise RuntimeError(f"No ffprobe statistics returned for {self.db_path}")
            return FfprobeStats(*row)
        except Exception:
            logger.exception("Failed to get ffprobe stats from %s", self.db_path)
            raise

    def delete_meta_for_file(self, media_file_id: int) -> None:
        """Remove all ffprobe metadata for a single media file."""

        def _delete(con):
            con.execute(db_query.DbQuery.FfprobeVideo.DELETE_BY_FILE, (media_file_id,))
            con.execute(db_query.DbQuery.FfprobeAudio.DELETE_BY_FILE, (media_file_id,))
            con.execute(
                db_query.DbQuery.FfprobeSubtitle.DELETE_BY_FILE, (media_file_id,)
            )

        self._run_in_transaction(_delete)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError, TypeError:
            return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError, TypeError:
            return None
