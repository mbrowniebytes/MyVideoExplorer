from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.folder_list.folder_hierarchy import (
    build_folder_rows,
    merge_folder_rows,
)
from MyVideoExplorer.utils.file_util_model import FileUtilModel

logger = logging.getLogger(__name__)


class DbFilter:
    """High-performance database-backed filtering using DuckDB vectorized execution."""

    def __init__(self, settings_state: Any) -> None:
        self.settings_state = settings_state

    @staticmethod
    def _normalize_path(path: str) -> str:
        normalized = str(path).strip().replace("\\", "/")
        while len(normalized) > 1 and normalized.endswith("/"):
            if len(normalized) == 3 and normalized[1] == ":":
                break
            normalized = normalized[:-1]
        return normalized.casefold()

    @staticmethod
    def _is_same_or_descendant(path: str, root: str) -> bool:
        if path == root:
            return True
        prefix = root if root.endswith("/") else f"{root}/"
        return path.startswith(prefix)

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
                            year_int = int(str(v).strip())
                            type_conditions.append("year = ?")
                            parameters.append(year_int)
                        except ValueError, TypeError:
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

            if type_conditions:
                # Disjunction within the same filter category (OR)
                where_groups.append(f"({' OR '.join(type_conditions)})")

        base_sql = "SELECT file_path FROM media_file"
        if where_groups:
            sql = f"{base_sql} WHERE {' AND '.join(where_groups)} ORDER BY lower(file_path)"
        else:
            sql = f"{base_sql} ORDER BY lower(file_path)"

        return sql, parameters

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

            if not db_path or not Path(db_path).is_file():
                continue

            db_path_posix = Path(db_path).as_posix()
            resolved_db = Path(db_path).resolve().as_posix().casefold()
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
                normalized_file_path = str(file_path).replace("\\", "/")
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
