from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.folder_list.folder_hierarchy import (
    build_folder_rows,
    merge_folder_rows,
)
from MyVideoExplorer.utils.file_util import FileUtils
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.file_util_type import FileUtilType

logger = logging.getLogger(__name__)


class DbFilter:
    """High-performance database-backed filtering using DuckDB vectorized execution."""

    def __init__(
        self, settings_state: Any, path_utils: FileUtils | None = None
    ) -> None:
        self.settings_state = settings_state
        self.path_utils = path_utils or FileUtils()

    @staticmethod
    def _build_last_played_condition(
        value: str,
    ) -> tuple[str, list[Any]] | None:
        """Build a SQL condition for last_played date filtering.

        Supports preset keys (never, yesterday, last_week, last_month, last_year)
        and custom format: custom|<op>|<date>.
        """
        if not value:
            return None

        today = datetime.now(UTC).date()

        if value == "never":
            return "last_played IS NULL", []
        if value == "yesterday":
            y = today - timedelta(days=1)
            return "last_played = ?", [y]
        if value == "last_week":
            start = today - timedelta(days=7)
            return "last_played >= ? AND last_played <= ?", [start, today]
        if value == "last_month":
            # Previous calendar month: 1st to last day
            first_of_this = today.replace(day=1)
            last_of_prev = first_of_this - timedelta(days=1)
            first_of_prev = last_of_prev.replace(day=1)
            return "last_played >= ? AND last_played <= ?", [
                first_of_prev,
                last_of_prev,
            ]
        if value == "last_year":
            # Previous calendar year: Jan 1 to Dec 31
            prev_year = today.year - 1
            start = date(prev_year, 1, 1)
            end = date(prev_year, 12, 31)
            return "last_played >= ? AND last_played <= ?", [start, end]
        if value.startswith("custom|"):
            parts = value.split("|")
            if len(parts) >= 3:
                op = parts[1]
                try:
                    target = date.fromisoformat(parts[2])
                except ValueError:
                    return None
                if op in {"=", "!=", ">", ">=", "<", "<="}:
                    return f"last_played {op} ?", [target]
            return None

        return None

    @staticmethod
    def _build_qty_played_condition(
        value: str,
    ) -> tuple[str, list[Any]] | None:
        """Build a SQL condition for qty_played filtering.

        Supports preset keys (0, 1, 2, 3, 5, <12, <50, <100, >100)
        and custom format: custom|<op>|<number>.
        """
        if not value:
            return None

        if value.startswith("custom|"):
            parts = value.split("|")
            if len(parts) >= 3:
                op = parts[1]
                try:
                    num = int(parts[2])
                except ValueError:
                    return None
                if op in {"=", "!=", ">", ">=", "<", "<="}:
                    return f"coalesce(qty_played, 0) {op} ?", [num]
            return None

        # Preset values
        if value.startswith("<"):
            try:
                num = int(value[1:])
                return "coalesce(qty_played, 0) < ?", [num]
            except ValueError:
                return None
        elif value.startswith(">"):
            try:
                num = int(value[1:])
                return "coalesce(qty_played, 0) > ?", [num]
            except ValueError:
                return None
        else:
            try:
                num = int(value)
                return "coalesce(qty_played, 0) = ?", [num]
            except ValueError:
                return None

    @staticmethod
    def _normalize_path(path: str) -> str:
        return FileUtils.normalize_path(path).casefold()

    @staticmethod
    def _is_same_or_descendant(path: str, root: str) -> bool:
        return FileUtils.is_same_or_descendant(path, root)

    def build_query(self, filters: list[dict[str, Any]]) -> tuple[str, list[Any]]:
        """Construct a parameterized DuckDB SQL query from filter table criteria."""
        grouped: dict[str, list[Any]] = defaultdict(list)
        for f in filters:
            ftype = str(f.get("filter", "")).strip().casefold()
            fval = f.get("value")
            if fval is None or ftype in {"", "media"}:
                continue
            grouped[ftype].append(fval)

        where_groups: list[str] = []
        parameters: list[Any] = []

        for ftype, values in grouped.items():
            type_conditions: list[str] = []

            for val in values:
                # Handle lists or comma-separated values for tags/genres
                sub_values: list[str] = []
                if isinstance(val, (list, tuple, set)):
                    sub_values = [str(v).strip() for v in val if str(v).strip()]
                elif isinstance(val, str) and ("," in val or ";" in val):
                    sub_values = [
                        part.strip()
                        for part in val.replace(";", ",").split(",")
                        if part.strip()
                    ]
                else:
                    text_val = str(val).strip()
                    if text_val:
                        sub_values = [text_val]

                # Filter out placeholder texts
                sub_values = [v for v in sub_values if v.casefold() != "- select tag -"]

                if not sub_values and ftype != "year":
                    continue

                if ftype == "folder":
                    for v in sub_values:
                        type_conditions.append(
                            "contains(lower(list_extract(string_split("
                            "replace(file_path, chr(92), '/'), '/'), -2)), ?)"
                        )
                        parameters.append(v.casefold())

                elif ftype == "file":
                    for v in sub_values:
                        type_conditions.append(
                            "contains(lower(list_extract(string_split("
                            "replace(file_path, chr(92), '/'), '/'), -1)), ?)"
                        )
                        parameters.append(v.casefold())

                elif ftype == "title":
                    for v in sub_values:
                        type_conditions.append(
                            "contains(lower(coalesce(title, '')), ?)"
                        )
                        parameters.append(v.casefold())

                elif ftype == "genre":
                    for v in sub_values:
                        type_conditions.append(
                            "EXISTS (SELECT 1 FROM unnest(coalesce(genres, [])) AS g(val) "
                            "WHERE lower(g.val) = ? OR contains(lower(g.val), ?))"
                        )
                        parameters.append(v.casefold())
                        parameters.append(v.casefold())

                elif ftype == "tag":
                    for v in sub_values:
                        type_conditions.append(
                            "EXISTS (SELECT 1 FROM unnest("
                            "list_concat(coalesce(tags, []), coalesce(user_tags, []))"
                            ") AS t(val) WHERE lower(t.val) = ? OR contains(lower(t.val), ?))"
                        )
                        parameters.append(v.casefold())
                        parameters.append(v.casefold())

                elif ftype == "actor":
                    for v in sub_values:
                        type_conditions.append(
                            "EXISTS (SELECT 1 FROM unnest(coalesce(actors, [])) AS a(val) "
                            "WHERE contains(lower(a.val), ?))"
                        )
                        parameters.append(v.casefold())

                elif ftype == "director":
                    for v in sub_values:
                        type_conditions.append(
                            "EXISTS (SELECT 1 FROM unnest(coalesce(directors, [])) AS d(val) "
                            "WHERE contains(lower(d.val), ?))"
                        )
                        parameters.append(v.casefold())

                elif ftype == "year":
                    for v in sub_values or ([val] if val is not None else []):
                        try:
                            text = str(v).strip()
                            if text.startswith("custom|"):
                                _, op, raw_year = text.split("|", 2)
                                year_int = int(raw_year)
                                if op not in {"=", "!=", ">", ">=", "<", "<="}:
                                    continue
                            else:
                                op, year_int = "=", int(text)
                            type_conditions.append(f"year {op} ?")
                            parameters.append(year_int)
                        except ValueError:
                            continue

                elif ftype == "nfo":
                    for v in sub_values:
                        type_conditions.append(
                            "("
                            "contains(lower(coalesce(title, '')), ?) OR "
                            "contains(lower(coalesce(plot, '')), ?) OR "
                            "EXISTS (SELECT 1 FROM unnest(coalesce(genres, [])) AS g(val) WHERE contains(lower(g.val), ?)) OR "
                            "EXISTS (SELECT 1 FROM unnest(coalesce(actors, [])) AS a(val) WHERE contains(lower(a.val), ?)) OR "
                            "EXISTS (SELECT 1 FROM unnest(coalesce(directors, [])) AS d(val) WHERE contains(lower(d.val), ?)) OR "
                            "EXISTS (SELECT 1 FROM unnest(list_concat(coalesce(tags, []), coalesce(user_tags, []))) AS t(val) WHERE contains(lower(t.val), ?))"
                            ")"
                        )
                        parameters.extend([v.casefold()] * 6)

                elif ftype == "last played":
                    for v in sub_values or ([val] if val is not None else []):
                        condition = self._build_last_played_condition(str(v))
                        if condition is not None:
                            cond_sql, cond_params = condition
                            type_conditions.append(cond_sql)
                            parameters.extend(cond_params)

                elif ftype == "qty played":
                    for v in sub_values or ([val] if val is not None else []):
                        condition = self._build_qty_played_condition(str(v))
                        if condition is not None:
                            cond_sql, cond_params = condition
                            type_conditions.append(cond_sql)
                            parameters.extend(cond_params)

            if type_conditions:
                # Disjunction within the same filter category (OR)
                where_groups.append(f"({' OR '.join(type_conditions)})")

        base_sql = "SELECT file_path FROM media_file"
        if where_groups:
            sql = f"{base_sql} WHERE {' AND '.join(where_groups)} ORDER BY lower(file_path)"
        else:
            sql = f"{base_sql} ORDER BY lower(file_path)"

        return sql, parameters

    def count_filtered_media_folders(
        self, filters: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Count filtered folder rows independently in each configured media DB."""
        media_filters: set[str] = set()
        criteria = []
        for filter_item in filters:
            if str(filter_item.get("filter", "")).strip().casefold() != "media":
                criteria.append(filter_item)
                continue
            value = filter_item.get("value")
            values = value if isinstance(value, (list, tuple, set)) else [value]
            media_filters.update(
                self._normalize_path(str(path))
                for path in values
                if path and str(path).strip()
            )

        match_sql, match_params = self.build_query(criteria)
        counts: dict[str, int] = {}

        for config in getattr(self.settings_state, "media_configs", []) or []:
            configured_root = str(config.get("path", ""))
            media_folder = self.path_utils.normalize_path(configured_root)
            root = media_folder.casefold()
            if not media_folder:
                continue
            counts[root] = 0

            if media_filters and not any(
                self._is_same_or_descendant(root, media_root)
                or self._is_same_or_descendant(media_root, root)
                for media_root in media_filters
            ):
                continue

            db_path = self.settings_state.get_db_path(config)
            normalized_db_path = self.path_utils.normalize_path(db_path)
            if not Path(normalized_db_path).is_file():
                continue

            connection = duckdb.connect(normalized_db_path, read_only=True)
            try:
                rows = connection.execute(match_sql, match_params).fetchall()
            except Exception:
                logger.exception(
                    "DbFilter media-folder count query failed on %s",
                    normalized_db_path,
                )
                raise
            finally:
                connection.close()

            matched_folders: set[str] = set()
            for (file_path,) in rows:
                if not file_path:
                    continue
                normalized_file_path = self.path_utils.normalize_path(file_path)
                normalized_file_fold = self._normalize_path(normalized_file_path)
                if not self._is_same_or_descendant(normalized_file_fold, root):
                    continue
                if media_filters and not any(
                    self._is_same_or_descendant(normalized_file_fold, media_root)
                    for media_root in media_filters
                ):
                    continue
                matched_folders.update(
                    folder.full_path.casefold()
                    for folder in build_folder_rows(
                        normalized_file_path, configured_root
                    )
                )
            counts[root] = len(matched_folders)

        return counts

    def filter(
        self,
        filters: list[dict[str, Any]],
        selected_folders: list[str] | None = None,
    ) -> list[FileUtilModel]:
        """Execute filter query against configured media databases and return matching directory models."""
        # Extract any active media filters
        media_filters: set[str] = set()
        for f in filters:
            if str(f.get("filter", "")).strip().casefold() == "media":
                val = f.get("value")
                if isinstance(val, (list, tuple, set)):
                    for v in val:
                        norm = self._normalize_path(str(v))
                        if norm:
                            media_filters.add(norm)
                elif val:
                    norm = self._normalize_path(str(val))
                    if norm:
                        media_filters.add(norm)

        normalized_selected: set[str] = set()
        if selected_folders:
            normalized_selected = {
                self._normalize_path(str(p)) for p in selected_folders if str(p).strip()
            }

        sql, parameters = self.build_query(filters)
        folder_items: list[FileUtilModel] = []
        visited_dbs: set[tuple[str, str]] = set()
        folders_by_root: dict[str, dict[str, FileUtilModel]] = {}

        media_configs = getattr(self.settings_state, "media_configs", []) or []
        for config in media_configs:
            configured_root = str(config.get("path", ""))
            cfg_path = self._normalize_path(configured_root)

            # Skip if explicitly filtered by selected_folders
            if normalized_selected and cfg_path not in normalized_selected:
                continue

            # Skip if filtered by media buttons
            if media_filters and not any(
                self._is_same_or_descendant(cfg_path, media_root)
                or self._is_same_or_descendant(media_root, cfg_path)
                for media_root in media_filters
            ):
                continue

            db_path = None
            if hasattr(self.settings_state, "get_db_path"):
                db_path = self.settings_state.get_db_path(config)

            if (
                not db_path
                or not Path(self.path_utils.normalize_path(db_path)).is_file()
            ):
                continue

            db_path_posix = self.path_utils.normalize_path(db_path)
            resolved_db = self.path_utils.resolve_path(db_path).casefold()
            db_root_key = (resolved_db, cfg_path)
            if db_root_key in visited_dbs:
                continue
            visited_dbs.add(db_root_key)

            connection = duckdb.connect(db_path_posix)
            try:
                rows = connection.execute(sql, parameters).fetchall()
            except Exception:
                logger.exception("DbFilter query failed on %s", db_path_posix)
                raise
            finally:
                connection.close()

            folders_by_path = folders_by_root.setdefault(cfg_path, {})
            for (file_path,) in rows:
                if not file_path:
                    continue
                normalized_file_path = self.path_utils.normalize_path(file_path)
                normalized_file_fold = self._normalize_path(normalized_file_path)
                if media_filters and not any(
                    self._is_same_or_descendant(normalized_file_fold, media_root)
                    for media_root in media_filters
                ):
                    continue
                if cfg_path and not self._is_same_or_descendant(
                    normalized_file_fold, cfg_path
                ):
                    continue
                merge_folder_rows(
                    folder_items,
                    folders_by_path,
                    build_folder_rows(normalized_file_path, configured_root),
                )

        return sorted(folder_items, key=lambda item: item.full_path.casefold())

    def matching_videos(
        self,
        filters: list[dict[str, Any]],
        sort_option: str = "default",
    ) -> list[dict[str, Any]]:
        """Return matching video records with stable per-library identity."""
        media_filters: set[str] = set()
        criteria: list[dict[str, Any]] = []
        for filter_item in filters:
            if str(filter_item.get("filter", "")).strip().casefold() != "media":
                criteria.append(filter_item)
                continue
            value = filter_item.get("value")
            values = value if isinstance(value, (list, tuple, set)) else [value]
            media_filters.update(
                self._normalize_path(str(path))
                for path in values
                if path and str(path).strip()
            )

        match_sql, match_params = self.build_query(criteria)
        matches: list[dict[str, Any]] = []
        seen_databases: set[tuple[str, str]] = set()

        for config in getattr(self.settings_state, "media_configs", []) or []:
            configured_root = str(config.get("path", ""))
            media_folder = self.path_utils.normalize_path(configured_root)
            root = media_folder.casefold()
            if not media_folder:
                continue
            if media_filters and not any(
                self._is_same_or_descendant(root, media_root)
                or self._is_same_or_descendant(media_root, root)
                for media_root in media_filters
            ):
                continue

            db_path = self.settings_state.get_db_path(config)
            normalized_db_path = self.path_utils.normalize_path(db_path)
            if not Path(normalized_db_path).is_file():
                continue
            resolved_db = self.path_utils.resolve_path(db_path).casefold()
            db_key = (resolved_db, root)
            if db_key in seen_databases:
                continue
            seen_databases.add(db_key)

            connection = duckdb.connect(normalized_db_path, read_only=True)
            try:
                matched_paths = [
                    self.path_utils.normalize_path(row[0])
                    for row in connection.execute(match_sql, match_params).fetchall()
                    if row[0]
                    and self._is_same_or_descendant(
                        self._normalize_path(str(row[0])), root
                    )
                    and (
                        not media_filters
                        or any(
                            self._is_same_or_descendant(
                                self._normalize_path(str(row[0])), media_root
                            )
                            for media_root in media_filters
                        )
                    )
                ]
                if not matched_paths:
                    continue
                records = connection.execute(
                    """
                    SELECT id, file_path, title, last_played, qty_played
                    FROM media_file
                    WHERE file_path IN (SELECT unnest(?::VARCHAR[]))
                    """,
                    (matched_paths,),
                ).fetchall()
            except Exception:
                logger.exception(
                    "DbFilter matching-video query failed on %s", normalized_db_path
                )
                raise
            finally:
                connection.close()

            configured_root_path = Path(self.path_utils.normalize_path(configured_root))
            for media_id, file_path, title, last_played, qty_played in records:
                normalized_file_path = self.path_utils.normalize_path(file_path)
                if (
                    media_id is None
                    or Path(normalized_file_path).suffix.casefold()
                    not in FileUtilType.VIDEO_EXTS
                ):
                    continue
                try:
                    relative_path = Path(normalized_file_path).relative_to(
                        configured_root_path
                    )
                except ValueError:
                    continue
                matches.append(
                    {
                        "media_folder": media_folder,
                        "media_id": int(media_id),
                        "rel_path": self.path_utils.normalize_path(relative_path),
                        "file_path": normalized_file_path,
                        "title": title or Path(normalized_file_path).stem,
                        "last_played": last_played,
                        "qty_played": int(qty_played or 0),
                        "status": "exists",
                    }
                )

        if sort_option == "a_z":
            matches.sort(
                key=lambda row: (
                    str(row["title"]).casefold(),
                    str(row["file_path"]).casefold(),
                )
            )
        elif sort_option == "z_a":
            matches.sort(
                key=lambda row: (
                    str(row["title"]).casefold(),
                    str(row["file_path"]).casefold(),
                ),
                reverse=True,
            )
        elif sort_option == "last_played":
            matches.sort(
                key=lambda row: (
                    str(row["title"]).casefold(),
                    str(row["file_path"]).casefold(),
                )
            )
            matches.sort(
                key=lambda row: (
                    row["last_played"] is not None,
                    str(row["last_played"] or ""),
                ),
                reverse=True,
            )
        elif sort_option == "qty_played":
            matches.sort(
                key=lambda row: (
                    str(row["title"]).casefold(),
                    str(row["file_path"]).casefold(),
                )
            )
            matches.sort(
                key=lambda row: int(row["qty_played"]),
                reverse=True,
            )
        else:
            matches.sort(key=lambda row: str(row["file_path"]).casefold())
        return matches
