from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.db.db_filter import DbFilter
from MyVideoExplorer.utils.file_util import FileUtils

logger = logging.getLogger(__name__)

DEFAULT_FILTER_DB_PATH = Path("db") / "filter_catalog.db"


class DbFilters:
    """Persist saved filter definitions and their cached filtered-folder counts."""

    def __init__(
        self,
        settings_state: Any,
        legacy_filters: list[dict[str, Any]],
        db_path: Path | str = DEFAULT_FILTER_DB_PATH,
        path_utils: FileUtils | None = None,
    ) -> None:
        self.settings_state = settings_state
        self.db_path = Path(db_path)
        self.path_utils = path_utils or FileUtils()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_filter = DbFilter(settings_state, self.path_utils)
        self._initialize(legacy_filters)

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.path_utils.normalize_path(self.db_path))

    def _initialize(self, legacy_filters: list[dict[str, Any]]) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS media_filters (
                    filter_id UUID PRIMARY KEY DEFAULT uuid(),
                    name TEXT NOT NULL UNIQUE,
                    criteria JSON NOT NULL,
                    folder_counts MAP(VARCHAR, BIGINT) NOT NULL,
                    total_count BIGINT,
                    sort_order INTEGER NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS filter_store_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            imported = con.execute(
                "SELECT 1 FROM filter_store_meta WHERE key = 'legacy_json_imported'"
            ).fetchone()
            if imported:
                return

            con.begin()
            try:
                self._replace_all(con, legacy_filters)
                con.execute(
                    "INSERT INTO filter_store_meta (key, value) VALUES "
                    "('legacy_json_imported', 'true')"
                )
                con.commit()
            except Exception:
                con.rollback()
                raise

    @staticmethod
    def _serialize_criteria(criteria: list[dict[str, Any]]) -> str:
        return json.dumps(criteria, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _normalize_record(record: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        name = str(record.get("name", "")).strip()
        criteria = record.get("filters", [])
        if not name or not isinstance(criteria, list):
            raise ValueError("Saved filters must have a name and a criteria list.")
        return name, criteria

    def _replace_all(
        self, con: duckdb.DuckDBPyConnection, records: list[dict[str, Any]]
    ) -> None:
        existing_rows = con.execute(
            "SELECT filter_id, name, criteria, folder_counts, total_count "
            "FROM media_filters"
        ).fetchall()
        existing = {
            row[1]: {
                "filter_id": row[0],
                "criteria": json.loads(row[2]),
                "folder_counts": row[3] or {},
                "total_count": row[4],
            }
            for row in existing_rows
        }

        seen: set[str] = set()
        for order, record in enumerate(records):
            name, criteria = self._normalize_record(record)
            if name in seen:
                raise ValueError(f"Duplicate saved filter name: {name}")
            seen.add(name)
            old = existing.get(name)
            if old and old["criteria"] == criteria:
                folder_counts = old["folder_counts"]
                total_count = old["total_count"]
            else:
                folder_counts = {}
                total_count = None

            keys = list(folder_counts)
            values = [int(folder_counts[key]) for key in keys]
            con.execute(
                """
                INSERT INTO media_filters
                    (name, criteria, folder_counts, total_count, sort_order)
                VALUES (?, ?::JSON, map(?::VARCHAR[], ?::BIGINT[]), ?, ?)
                ON CONFLICT (name) DO UPDATE SET
                    criteria = excluded.criteria,
                    folder_counts = excluded.folder_counts,
                    total_count = excluded.total_count,
                    sort_order = excluded.sort_order
                """,
                (
                    name,
                    self._serialize_criteria(criteria),
                    keys,
                    values,
                    total_count,
                    order,
                ),
            )

        if seen:
            con.execute(
                "DELETE FROM media_filters WHERE name NOT IN (SELECT unnest(?))",
                (list(seen),),
            )
        else:
            con.execute("DELETE FROM media_filters")

    def list_filters(self) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT name, criteria, folder_counts, total_count "
                "FROM media_filters ORDER BY sort_order, lower(name)"
            ).fetchall()
        return [
            {
                "name": name,
                "filters": json.loads(criteria),
                "folder_counts": dict(folder_counts or {}),
                "total_count": total_count,
            }
            for name, criteria, folder_counts, total_count in rows
        ]

    def replace_all(self, records: list[dict[str, Any]]) -> None:
        with self._connect() as con:
            con.begin()
            try:
                self._replace_all(con, records)
                con.commit()
            except Exception:
                con.rollback()
                raise

    def save_filter(
        self,
        name: str,
        criteria: list[dict[str, Any]],
        original_name: str | None = None,
    ) -> None:
        name = name.strip()
        if not name:
            raise ValueError("A saved filter name cannot be empty.")
        serialized = self._serialize_criteria(criteria)

        with self._connect() as con:
            con.begin()
            try:
                old_name = original_name or name
                old = con.execute(
                    "SELECT filter_id, criteria FROM media_filters WHERE name = ?",
                    (old_name,),
                ).fetchone()
                conflict = con.execute(
                    "SELECT filter_id FROM media_filters WHERE name = ?",
                    (name,),
                ).fetchone()
                if conflict and (old is None or conflict[0] != old[0]):
                    con.execute("DELETE FROM media_filters WHERE name = ?", (name,))

                if old:
                    same_criteria = json.loads(old[1]) == criteria
                    if same_criteria:
                        con.execute(
                            "UPDATE media_filters SET name = ? WHERE filter_id = ?",
                            (name, old[0]),
                        )
                    else:
                        con.execute(
                            """
                            UPDATE media_filters
                            SET name = ?, criteria = ?::JSON,
                                folder_counts = map(?::VARCHAR[], ?::BIGINT[]),
                                total_count = NULL
                            WHERE filter_id = ?
                            """,
                            (name, serialized, [], [], old[0]),
                        )
                else:
                    order_row = con.execute(
                        "SELECT coalesce(max(sort_order), -1) + 1 FROM media_filters"
                    ).fetchone()
                    if order_row is None:
                        raise RuntimeError("Unable to determine saved-filter ordering.")
                    next_order = order_row[0]
                    con.execute(
                        """
                        INSERT INTO media_filters
                            (name, criteria, folder_counts, total_count, sort_order)
                        VALUES (?, ?::JSON, map(?::VARCHAR[], ?::BIGINT[]), NULL, ?)
                        """,
                        (name, serialized, [], [], next_order),
                    )
                con.commit()
            except Exception:
                con.rollback()
                raise

    def delete_filter(self, name: str) -> None:
        with self._connect() as con:
            deleted = con.execute(
                "DELETE FROM media_filters WHERE name = ? RETURNING name", (name,)
            ).fetchone()
        if deleted is None:
            raise KeyError(f"Saved filter does not exist: {name}")

    def get_filter(self, name: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT name, criteria, folder_counts, total_count "
                "FROM media_filters WHERE name = ?",
                (name,),
            ).fetchone()
        if row is None:
            return None
        return {
            "name": row[0],
            "filters": json.loads(row[1]),
            "folder_counts": dict(row[2] or {}),
            "total_count": row[3],
        }

    def get_display_count(
        self, name: str, selected_folders: list[str] | None = None
    ) -> int | None:
        record = self.get_filter(name)
        if record is None:
            return None
        total_count = record["total_count"]
        folder_counts = record["folder_counts"]
        if total_count is None:
            return None

        configured = {
            self.path_utils.normalize_path(str(config.get("path", ""))).casefold()
            for config in (getattr(self.settings_state, "media_configs", []) or [])
            if config.get("path")
        }
        selected = {
            self.path_utils.normalize_path(str(path)).casefold()
            for path in (selected_folders or [])
            if str(path).strip()
        }
        if not selected or configured.issubset(selected):
            return int(total_count)

        counts_by_path = {
            self.path_utils.normalize_path(str(path)).casefold(): int(count)
            for path, count in folder_counts.items()
        }
        return sum(counts_by_path.get(path, 0) for path in selected)

    def refresh_filter_counts(self, name: str) -> dict[str, Any]:
        record = self.get_filter(name)
        if record is None:
            raise KeyError(f"Saved filter does not exist: {name}")

        counts = self.db_filter.count_filtered_media_folders(record["filters"])
        keys = list(counts)
        values = [counts[key] for key in keys]
        total = sum(values)
        with self._connect() as con:
            updated = con.execute(
                """
                UPDATE media_filters
                SET folder_counts = map(?::VARCHAR[], ?::BIGINT[]),
                    total_count = ?
                WHERE name = ?
                RETURNING name
                """,
                (keys, values, total, name),
            ).fetchone()
        if updated is None:
            raise KeyError(f"Saved filter does not exist: {name}")
        logger.debug("Refreshed media-folder counts for filter %s: %s", name, total)
        refreshed = self.get_filter(name)
        if refreshed is None:
            raise RuntimeError(f"Saved filter disappeared after refresh: {name}")
        return refreshed
