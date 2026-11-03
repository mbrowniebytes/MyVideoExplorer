from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.db.db_backup import backup_database
from MyVideoExplorer.db.db_filter import DbFilter
from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.db_snowflake_id import SnowflakeIdGenerator
from MyVideoExplorer.tag_cloud.tag_util import validate_name
from MyVideoExplorer.utils.file_util import FileUtils

logger = logging.getLogger(__name__)

DEFAULT_FILTER_DB_PATH = Path("db") / "filter_catalog.db"
FILTER_SORT_OPTIONS = {
    "default",
    "manual",
    "a_z",
    "z_a",
    "last_played",
    "qty_played",
}


class DbFilters:
    """Persist saved filters, cached counts, and optional manual video ordering."""

    def __init__(
        self,
        settings_state: Any,
        db_path: Path | str = DEFAULT_FILTER_DB_PATH,
        path_utils: FileUtils | None = None,
    ) -> None:
        self.settings_state = settings_state
        self.db_path = Path(db_path)
        self.path_utils = path_utils or FileUtils()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_filter = DbFilter(settings_state, self.path_utils)
        self._initialize()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.path_utils.normalize_path(self.db_path))

    def _initialize(self) -> None:
        DbMigrations(str(self.db_path), db_type="filter_catalog").run_migrations()

    @staticmethod
    def _serialize_criteria(criteria: list[dict[str, Any]]) -> str:
        return json.dumps(criteria, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _normalize_record(
        record: dict[str, Any],
    ) -> tuple[str, list[dict[str, Any]], str]:
        name = str(record.get("name", "")).strip()
        criteria = record.get("filters", [])
        sort_option = str(record.get("sort_option", "default"))
        if not name or not isinstance(criteria, list):
            raise ValueError("Saved filters must have a name and a criteria list.")
        if sort_option not in FILTER_SORT_OPTIONS:
            raise ValueError(f"Unknown saved-filter sort option: {sort_option}")
        return name, criteria, sort_option

    @staticmethod
    def _replace_manual_list(
        con: duckdb.DuckDBPyConnection,
        filter_id: int,
        items: list[dict[str, Any]],
    ) -> None:
        con.execute(
            """
            UPDATE filter_manual_list
            SET order_index = -order_index - 1
            WHERE filter_id = ?
            """,
            (filter_id,),
        )
        con.execute("DELETE FROM filter_manual_list WHERE filter_id = ?", (filter_id,))
        for order_index, item in enumerate(items, start=1):
            media_folder = str(item.get("media_folder", "")).strip()
            rel_path = FileUtils.normalize_path(str(item.get("rel_path", "")))
            media_id = item.get("media_id")
            status = str(item.get("status", "exists"))
            if (
                not media_folder
                or not rel_path
                or media_id is None
                or status not in {"exists", "missing"}
            ):
                raise ValueError("Manual filter entries require valid identity data.")
            con.execute(
                """
                INSERT INTO filter_manual_list
                    (filter_id, order_index, media_folder, media_id, rel_path, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (filter_id, order_index, media_folder, int(media_id), rel_path, status),
            )

    def _replace_all(
        self, con: duckdb.DuckDBPyConnection, records: list[dict[str, Any]]
    ) -> None:
        existing_rows = con.execute(
            "SELECT filter_id, name, criteria, folder_counts, total_count, "
            "sort_option, needs_rebuild "
            "FROM media_filters"
        ).fetchall()
        existing = {
            row[1]: {
                "filter_id": row[0],
                "criteria": json.loads(row[2]),
                "folder_counts": row[3] or {},
                "total_count": row[4],
                "sort_option": row[5],
                "needs_rebuild": row[6],
            }
            for row in existing_rows
        }

        seen: set[str] = set()
        for order, record in enumerate(records):
            name, criteria, sort_option = self._normalize_record(record)
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
            filter_id = old["filter_id"] if old else SnowflakeIdGenerator().generate()
            needs_rebuild = bool(old and old["needs_rebuild"])
            if old and old["criteria"] != criteria and sort_option == "manual":
                needs_rebuild = True
            keys = list(folder_counts)
            values = [int(folder_counts[key]) for key in keys]
            con.execute(
                """
                INSERT INTO media_filters
                    (filter_id, name, criteria, folder_counts, total_count, sort_order,
                     sort_option, needs_rebuild)
                VALUES (?, ?, ?::JSON, map(?::VARCHAR[], ?::BIGINT[]), ?, ?, ?, ?)
                ON CONFLICT (name) DO UPDATE SET
                    criteria = excluded.criteria,
                    folder_counts = excluded.folder_counts,
                    total_count = excluded.total_count,
                    sort_order = excluded.sort_order,
                    sort_option = excluded.sort_option,
                    needs_rebuild = excluded.needs_rebuild
                """,
                (
                    filter_id,
                    name,
                    self._serialize_criteria(criteria),
                    keys,
                    values,
                    total_count,
                    order,
                    sort_option,
                    needs_rebuild,
                ),
            )

        if seen:
            con.execute(
                "DELETE FROM media_filters WHERE name NOT IN (SELECT unnest(?))",
                (list(seen),),
            )
        else:
            con.execute("DELETE FROM media_filters")
        con.execute(
            "DELETE FROM filter_manual_list "
            "WHERE filter_id NOT IN (SELECT filter_id FROM media_filters)"
        )

    def list_filters(self) -> list[dict[str, Any]]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT name, criteria, folder_counts, total_count "
                ", sort_option, needs_rebuild FROM media_filters "
                "ORDER BY sort_order, lower(name)"
            ).fetchall()
        return [
            {
                "name": name,
                "filters": json.loads(criteria),
                "folder_counts": dict(folder_counts or {}),
                "total_count": total_count,
                "sort_option": sort_option,
                "needs_rebuild": bool(needs_rebuild),
            }
            for name, criteria, folder_counts, total_count, sort_option, needs_rebuild in rows
        ]

    def replace_all(self, records: list[dict[str, Any]]) -> None:
        backup_database(str(self.db_path))
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
        sort_option: str = "default",
        manual_items: list[dict[str, Any]] | None = None,
    ) -> None:
        backup_database(str(self.db_path))
        name = name.strip()
        if not name:
            raise ValueError("A saved filter name cannot be empty.")

        # Validate name characters
        is_valid, error_msg = validate_name(name)
        if not is_valid:
            raise ValueError(error_msg)
        if sort_option not in FILTER_SORT_OPTIONS:
            raise ValueError(f"Unknown saved-filter sort option: {sort_option}")

        serialized = self._serialize_criteria(criteria)

        with self._connect() as con:
            con.begin()
            try:
                old_name = original_name or name
                old = con.execute(
                    "SELECT filter_id, criteria FROM media_filters WHERE name = ?",
                    (old_name,),
                ).fetchone()

                # Check for case-insensitive duplicate names
                existing_names = con.execute(
                    "SELECT name FROM media_filters"
                ).fetchall()
                existing_lower = {row[0].casefold() for row in existing_names}
                # Exclude the original name if this is a rename operation
                if original_name is not None:
                    existing_lower.discard(original_name.casefold())
                if name.casefold() in existing_lower:
                    raise ValueError(
                        f"A filter with the name '{name}' already exists. "
                        "Filter names must be unique (case-insensitive)."
                    )

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
                            "UPDATE media_filters SET name = ?, sort_option = ? "
                            "WHERE filter_id = ?",
                            (name, sort_option, old[0]),
                        )
                    else:
                        con.execute(
                            """
                            UPDATE media_filters
                            SET name = ?, criteria = ?::JSON,
                                folder_counts = map(?::VARCHAR[], ?::BIGINT[]),
                                total_count = NULL, sort_option = ?,
                                needs_rebuild = ?
                            WHERE filter_id = ?
                            """,
                            (
                                name,
                                serialized,
                                [],
                                [],
                                sort_option,
                                sort_option == "manual",
                                old[0],
                            ),
                        )
                    if manual_items is not None and sort_option == "manual":
                        self._replace_manual_list(con, int(old[0]), manual_items)
                        con.execute(
                            "UPDATE media_filters SET needs_rebuild = ? "
                            "WHERE filter_id = ?",
                            (
                                any(
                                    item.get("status", "exists") == "missing"
                                    for item in manual_items
                                ),
                                old[0],
                            ),
                        )
                else:
                    order_row = con.execute(
                        "SELECT coalesce(max(sort_order), -1) + 1 FROM media_filters"
                    ).fetchone()
                    if order_row is None:
                        raise RuntimeError("Unable to determine saved-filter ordering.")
                    next_order = order_row[0]
                    filter_id = SnowflakeIdGenerator().generate()
                    con.execute(
                        """
                        INSERT INTO media_filters
                            (filter_id, name, criteria, folder_counts, total_count,
                             sort_order, sort_option, needs_rebuild)
                        VALUES (?, ?, ?::JSON, map(?::VARCHAR[], ?::BIGINT[]), NULL,
                                ?, ?, ?)
                        """,
                        (
                            filter_id,
                            name,
                            serialized,
                            [],
                            [],
                            next_order,
                            sort_option,
                            sort_option == "manual" and manual_items is None,
                        ),
                    )
                    if manual_items is not None and sort_option == "manual":
                        self._replace_manual_list(con, filter_id, manual_items)
                        con.execute(
                            "UPDATE media_filters SET needs_rebuild = ? "
                            "WHERE filter_id = ?",
                            (
                                any(
                                    item.get("status", "exists") == "missing"
                                    for item in manual_items
                                ),
                                filter_id,
                            ),
                        )
                con.commit()
            except Exception:
                con.rollback()
                raise

    def delete_filter(self, name: str) -> None:
        backup_database(str(self.db_path))
        with self._connect() as con:
            con.begin()
            try:
                filter_row = con.execute(
                    "SELECT filter_id FROM media_filters WHERE name = ?", (name,)
                ).fetchone()
                if filter_row is not None:
                    con.execute(
                        "DELETE FROM filter_manual_list WHERE filter_id = ?",
                        (filter_row[0],),
                    )
                deleted = con.execute(
                    "DELETE FROM media_filters WHERE name = ? RETURNING name",
                    (name,),
                ).fetchone()
                con.commit()
            except Exception:
                con.rollback()
                raise
        if deleted is None:
            raise KeyError(f"Saved filter does not exist: {name}")

    def get_filter(self, name: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT name, criteria, folder_counts, total_count, sort_option, "
                "needs_rebuild "
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
            "sort_option": row[4],
            "needs_rebuild": bool(row[5]),
        }

    def get_manual_items(self, name: str) -> list[dict[str, Any]]:
        """Return a filter's persisted video rows in manual order."""
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT m.media_folder, m.media_id, m.rel_path, m.status
                FROM filter_manual_list AS m
                JOIN media_filters AS f ON f.filter_id = m.filter_id
                WHERE f.name = ?
                ORDER BY m.order_index
                """,
                (name,),
            ).fetchall()
        return [
            {
                "media_folder": media_folder,
                "media_id": int(media_id),
                "rel_path": rel_path,
                "status": status,
            }
            for media_folder, media_id, rel_path, status in rows
        ]

    def mark_manual_items_stale(self, media_folder: str) -> list[str]:
        """Mark manual entries missing when a scan removed or replaced their media ID."""
        root_path = self.path_utils.normalize_path(media_folder)
        root = root_path.casefold()
        configs = [
            config
            for config in (getattr(self.settings_state, "media_configs", []) or [])
            if self.path_utils.normalize_path(str(config.get("path", ""))).casefold()
            == root
        ]
        if not configs:
            raise ValueError(f"No configured media folder matches: {media_folder}")
        db_path = self.settings_state.get_db_path(configs[0])
        normalized_db_path = self.path_utils.normalize_path(db_path)
        if not Path(normalized_db_path).is_file():
            raise FileNotFoundError(
                f"Media database does not exist: {normalized_db_path}"
            )

        with self._connect() as con:
            entries = con.execute(
                """
                SELECT m.filter_id, m.media_id, m.rel_path, m.status
                FROM filter_manual_list AS m
                WHERE lower(m.media_folder) = ?
                """,
                (root,),
            ).fetchall()
        if not entries:
            return []

        expected_paths = [
            self.path_utils.normalize_path(f"{root_path}/{rel_path.lstrip('/')}")
            for _, _, rel_path, _ in entries
        ]
        with duckdb.connect(normalized_db_path, read_only=True) as media_con:
            resolved_rows = media_con.execute(
                """
                SELECT id, file_path
                FROM media_file
                WHERE lower(file_path) IN (
                    SELECT lower(unnest(?::VARCHAR[]))
                )
                """,
                (expected_paths,),
            ).fetchall()
        resolved = {
            self.path_utils.normalize_path(file_path).casefold(): int(media_id)
            for media_id, file_path in resolved_rows
        }

        stale_rows = [
            (int(filter_id), int(media_id))
            for filter_id, media_id, rel_path, status in entries
            if status != "missing"
            and resolved.get(
                self.path_utils.normalize_path(
                    f"{root_path}/{str(rel_path).lstrip('/')}"
                ).casefold()
            )
            != int(media_id)
        ]
        if not stale_rows:
            return []
        stale_filter_ids = sorted({filter_id for filter_id, _ in stale_rows})

        with self._connect() as con:
            con.begin()
            try:
                for filter_id, media_id in stale_rows:
                    con.execute(
                        """
                        UPDATE filter_manual_list
                        SET status = 'missing'
                        WHERE filter_id = ? AND media_id = ?
                          AND lower(media_folder) = ?
                        """,
                        (filter_id, media_id, root),
                    )
                rows = con.execute(
                    "SELECT name FROM media_filters "
                    "WHERE filter_id IN (SELECT unnest(?::BIGINT[]))",
                    (stale_filter_ids,),
                ).fetchall()
                names = [str(row[0]) for row in rows]
                con.execute(
                    """
                    UPDATE media_filters
                    SET needs_rebuild = TRUE
                    WHERE filter_id IN (SELECT unnest(?::BIGINT[]))
                    """,
                    (stale_filter_ids,),
                )
                con.commit()
            except Exception:
                con.rollback()
                raise
        return names

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

    def refresh_filter(self, name: str) -> dict[str, Any]:
        """Refresh cached counts and reconcile the expanded list for Manual filters."""
        record = self.get_filter(name)
        if record is None:
            raise KeyError(f"Saved filter does not exist: {name}")

        counts = self.db_filter.count_filtered_media_folders(record["filters"])
        manual_items: list[dict[str, Any]] | None = None
        if record["sort_option"] == "manual":
            matches = self.db_filter.matching_videos(record["filters"])
            existing = self.get_manual_items(name)
            match_by_identity = {
                (item["media_folder"].casefold(), int(item["media_id"])): item
                for item in matches
            }
            manual_items = []
            seen: set[tuple[str, int]] = set()
            for item in existing:
                identity = (item["media_folder"].casefold(), int(item["media_id"]))
                match = match_by_identity.get(identity)
                if match is None or match["rel_path"] != item["rel_path"]:
                    continue
                manual_items.append(match)
                seen.add(identity)
            for match in matches:
                identity = (match["media_folder"].casefold(), int(match["media_id"]))
                if identity not in seen:
                    manual_items.append(match)
                    seen.add(identity)

        keys = list(counts)
        values = [counts[key] for key in keys]
        total = sum(values)
        with self._connect() as con:
            con.begin()
            try:
                updated = con.execute(
                    """
                    UPDATE media_filters
                    SET folder_counts = map(?::VARCHAR[], ?::BIGINT[]),
                        total_count = ?,
                        needs_rebuild = CASE
                            WHEN sort_option = 'manual' THEN FALSE
                            ELSE needs_rebuild
                        END
                    WHERE name = ?
                    RETURNING filter_id
                    """,
                    (keys, values, total, name),
                ).fetchone()
                if updated is not None and manual_items is not None:
                    self._replace_manual_list(con, int(updated[0]), manual_items)
                con.commit()
            except Exception:
                con.rollback()
                raise
        if updated is None:
            raise KeyError(f"Saved filter does not exist: {name}")
        logger.debug("Refreshed saved filter %s: %s media folders", name, total)
        refreshed = self.get_filter(name)
        if refreshed is None:
            raise RuntimeError(f"Saved filter disappeared after refresh: {name}")
        return refreshed
