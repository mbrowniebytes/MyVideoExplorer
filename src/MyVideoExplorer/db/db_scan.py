import json
import logging
import re
from typing import Any

import duckdb

from MyVideoExplorer.db import db_migrations, db_query
from MyVideoExplorer.lang.lang_loader import LangLoader

logger = logging.getLogger(__name__)


class DbScanUtil:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lang = LangLoader.get_lang("en")
        self._init_db()

    @staticmethod
    def _normalize_array_value(value: Any) -> list[str] | None:
        if value is None:
            return None

        if isinstance(value, (list, tuple, set)):
            items: list[str] = []
            for item in value:
                if isinstance(item, dict):
                    extracted = (
                        item.get("name")
                        or item.get("title")
                        or item.get("value")
                        or item.get("role")
                    )
                    if extracted is not None:
                        text = str(extracted).strip()
                        if text:
                            items.append(text)
                else:
                    text = str(item).strip()
                    if text:
                        items.append(text)
            return items or None

        if not isinstance(value, str):
            value = str(value)

        text = value.strip()
        if not text:
            return None

        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return DbScanUtil._normalize_array_value(parsed)
            except json.JSONDecodeError:
                pass

        parts = re.split(r"[,;|\n]+", text)
        cleaned = [part.strip() for part in parts if part and part.strip()]
        return cleaned or None

    def _init_db(self):
        db_migrations.DbMigrations(self.db_path).run_migrations()

    def _run_in_transaction(self, operation):
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

    def save_stats(self, stats: dict[str, Any], progress_callback=None):
        if progress_callback is not None:
            progress_callback(0, self.lang.scan_progress["saving_stats"])

        def _save(con):
            con.execute(
                db_query.DbQuery.MediaPathStats.INSERT,
                (
                    stats["media_path"],
                    stats["subfolders_count"],
                    stats["files_count"],
                    stats["images_count"],
                    stats["videos_count"],
                    stats["nfo_count"],
                    stats["other_count"],
                    stats["last_scanned"],
                ),
            )

        self._run_in_transaction(_save)
        if progress_callback is not None:
            progress_callback(100, self.lang.scan_progress["saved_stats"])

    def get_stats(self, media_path: str):
        con = duckdb.connect(self.db_path)
        res = con.execute(
            db_query.DbQuery.MediaPathStats.SELECT, (media_path,)
        ).fetchone()
        con.close()
        return res

    def delete_stats(self, media_path: str):
        def _delete(con):
            con.execute(db_query.DbQuery.MediaPathStats.DELETE, (media_path,))

        self._run_in_transaction(_delete)

    def save_media(
        self, media_list: list[dict[str, Any]], media_path: str, progress_callback=None
    ):
        con = duckdb.connect(self.db_path)

        if progress_callback is not None:
            progress_callback(10, self.lang.scan_progress["cleaning_old_media_records"])

        try:
            # 1. Delete records for the scanned folder that are no longer present
            def _cleanup(con):
                if media_list:
                    incoming_paths = [item.get("file_path") for item in media_list]
                    con.execute(
                        db_query.DbQuery.MediaFile.DELETE_BY_DIR_NOT_IN,
                        (f"{media_path}%", incoming_paths),
                    )
                else:
                    self.delete_stats(media_path)

            if media_list:
                self._run_in_transaction(_cleanup)
            else:
                self.delete_stats(media_path)

            if not media_list:
                if progress_callback is not None:
                    progress_callback(100, self.lang.scan_progress["saved_media_rows"])
                con.close()
                return

            if progress_callback is not None:
                progress_callback(25, self.lang.scan_progress["preparing_media_rows"])

            data = []
            for item in media_list:
                metadata = item.get("metadata") or {}

                year = metadata.get("year")
                if year == "" or year is None:
                    year = None
                else:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = None

                runtime = metadata.get("runtime")
                if runtime == "" or runtime is None:
                    runtime = 0
                else:
                    try:
                        runtime = int(runtime) * 60
                    except (ValueError, TypeError):
                        runtime = 0

                data.append(
                    (
                        media_path,
                        item.get("file_path"),
                        item.get("type"),
                        metadata.get("title"),
                        year,
                        metadata.get("plot"),
                        metadata.get("score"),
                        metadata.get("rated"),
                        runtime,
                        self._normalize_array_value(metadata.get("tags")),
                        self._normalize_array_value(metadata.get("genres")),
                        self._normalize_array_value(metadata.get("actors")),
                        self._normalize_array_value(metadata.get("directors")),
                    )
                )

            batch_size = 200
            start_percent = 25
            finish_percent = 85
            offset_percent = finish_percent - start_percent
            total_rows = len(data)
            for batch_index in range(0, total_rows, batch_size):
                batch = data[batch_index : batch_index + batch_size]

                def _upsert_batch(batch_rows, connection):
                    connection.executemany(
                        db_query.DbQuery.MediaFile.UPSERT_MEDIA, batch_rows
                    )

                self._run_in_transaction(
                    lambda inner_con, batch_rows=batch: _upsert_batch(
                        batch_rows, inner_con
                    )
                )

                if progress_callback is not None:
                    percent = start_percent + int(
                        ((batch_index + len(batch)) / total_rows) * offset_percent
                    )
                    progress_callback(
                        percent, self.lang.scan_progress["saving_media_rows"]
                    )

            if progress_callback is not None:
                progress_callback(100, self.lang.scan_progress["saved_media_rows"])
        finally:
            con.close()
