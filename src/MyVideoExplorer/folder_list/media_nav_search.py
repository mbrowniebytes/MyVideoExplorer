from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.utils.file_util_model import FileUtilModel

TEXT_SEARCH_FIELDS = frozenset(
    {"folder_name", "file_name", "movie_name", "director", "actor"}
)
NAME_SEARCH_FIELDS = frozenset({"folder_name", "file_name", "movie_name"})
PERSON_SEARCH_FIELDS = frozenset({"director", "actor"})
ALL_SEARCH_FIELDS = {"tags", "year", "qty_played", "last_played"}
QTY_OPERATORS = {
    "=": "=",
    "!=": "!=",
    ">": ">",
    ">=": ">=",
    "<": "<",
    "<=": "<=",
}
DATE_OPERATORS = QTY_OPERATORS

_TEXT_EXPRESSIONS = {
    "folder_name": "lower(list_extract(string_split(file_path, '/'), -2))",
    "file_name": "lower(list_extract(string_split(file_path, '/'), -1))",
    "movie_name": "lower(coalesce(title, ''))",
    "director": "lower(array_to_string(coalesce(directors, []), ' '))",
    "actor": "lower(array_to_string(coalesce(actors, []), ' '))",
    "year": "lower(coalesce(CAST(year AS VARCHAR), ''))",
    "tags": "lower(array_to_string(list_concat(coalesce(tags, []), coalesce(user_tags, [])), ' '))",
}


@dataclass(frozen=True)
class MediaNavSearchCriteria:
    query: str
    fields: frozenset[str] = frozenset()
    tags: tuple[str, ...] = ()
    name_field: str = "movie_name"
    secondary_field: str | None = None
    secondary_query: str = ""
    year: int | None = None
    year_operator: str = "="
    qty_operator: str | None = None
    qty_value: int | None = None
    date_operator: str | None = None
    date_start: str | None = None

    def __post_init__(self) -> None:
        unknown_fields = self.fields - ALL_SEARCH_FIELDS
        if unknown_fields:
            raise ValueError(f"Unknown media search fields: {sorted(unknown_fields)}")
        if self.name_field not in NAME_SEARCH_FIELDS:
            raise ValueError(f"Unknown name search field: {self.name_field}")
        if (
            self.secondary_field is not None
            and self.secondary_field not in PERSON_SEARCH_FIELDS
        ):
            raise ValueError(f"Unknown secondary search field: {self.secondary_field}")
        if "year" in self.fields and (
            self.year_operator not in QTY_OPERATORS or self.year is None
        ):
            raise ValueError("Choose a valid Year operator and value.")
        if "qty_played" in self.fields and (
            self.qty_operator not in QTY_OPERATORS
            or self.qty_value is None
            or self.qty_value < 0
        ):
            raise ValueError("Choose a valid Qty Played operator and value.")
        if "last_played" in self.fields:
            if self.date_operator not in DATE_OPERATORS or not self.date_start:
                raise ValueError("Choose a valid Date Last Played operator and date.")

    @property
    def has_criteria(self) -> bool:
        return bool(
            self.query.strip()
            or (self.secondary_field and self.secondary_query.strip())
            or ("year" in self.fields and self.year is not None)
            or ("tags" in self.fields and self.tags)
            or ("qty_played" in self.fields and self.qty_value is not None)
            or ("last_played" in self.fields and self.date_start)
        )


class MediaNavSearch:
    """Search configured media databases and return matching parent folders."""

    def __init__(self, settings_state: Any) -> None:
        self.settings_state = settings_state

    def search(self, criteria: MediaNavSearchCriteria) -> list[FileUtilModel]:
        if not self.settings_state.db_enabled():
            raise RuntimeError(
                "Media database search requires an enabled, configured media database."
            )

        where: list[str] = []
        parameters: list[Any] = []
        query = criteria.query.strip().casefold()

        if query:
            where.append(f"contains({_TEXT_EXPRESSIONS[criteria.name_field]}, ?)")
            parameters.append(query)

        secondary_query = criteria.secondary_query.strip().casefold()
        if criteria.secondary_field and secondary_query:
            where.append(f"contains({_TEXT_EXPRESSIONS[criteria.secondary_field]}, ?)")
            parameters.append(secondary_query)

        if "year" in criteria.fields and criteria.year is not None:
            where.append(f"year {QTY_OPERATORS[criteria.year_operator]} ?")
            parameters.append(criteria.year)

        selected_tags = criteria.tags if "tags" in criteria.fields else ()
        for tag in dict.fromkeys(tag.strip() for tag in selected_tags if tag.strip()):
            where.append(
                "EXISTS (SELECT 1 FROM unnest("
                "list_concat(coalesce(tags, []), coalesce(user_tags, []))"
                ") AS item(tag) WHERE lower(item.tag) = ?)"
            )
            parameters.append(tag.casefold())

        if "qty_played" in criteria.fields:
            if criteria.qty_operator not in QTY_OPERATORS or criteria.qty_value is None:
                raise ValueError("Choose a valid Qty Played operator and value.")
            if criteria.qty_value < 0:
                raise ValueError("Qty Played must not be negative.")
            where.append(
                f"coalesce(qty_played, 0) {QTY_OPERATORS[criteria.qty_operator]} ?"
            )
            parameters.append(criteria.qty_value)

        if "last_played" in criteria.fields:
            if criteria.date_operator not in DATE_OPERATORS or not criteria.date_start:
                raise ValueError("Choose a valid Date Last Played operator and date.")
            try:
                date_start = date.fromisoformat(criteria.date_start)
            except ValueError as error:
                raise ValueError("Enter a valid Date Last Played value.") from error
            where.append(f"last_played {DATE_OPERATORS[criteria.date_operator]} ?")
            parameters.append(date_start)

        sql = "SELECT file_path FROM media_file WHERE "
        sql += " AND ".join(where)
        sql += " ORDER BY lower(file_path)"
        matches: dict[str, FileUtilModel] = {}
        visited_databases: set[str] = set()

        for config in self.settings_state.media_configs:
            db_path = self.settings_state.get_db_path(config)
            if not db_path or not Path(db_path).is_file():
                continue
            normalized_db = str(Path(db_path).resolve()).casefold()
            if normalized_db in visited_databases:
                continue
            visited_databases.add(normalized_db)

            with duckdb.connect(str(db_path), read_only=True) as connection:
                if criteria.has_criteria:
                    rows = connection.execute(sql, parameters).fetchall()
                else:
                    rows = connection.execute(
                        "SELECT file_path FROM media_file ORDER BY lower(file_path)"
                    ).fetchall()

            for (file_path,) in rows:
                if not file_path:
                    continue
                folder_path = Path(file_path).parent
                normalized_path = folder_path.as_posix().casefold()
                if normalized_path in matches:
                    continue
                name = folder_path.name or folder_path.as_posix()
                matches[normalized_path] = FileUtilModel(
                    type="dir",
                    name=name,
                    full_path=folder_path.as_posix(),
                    depth=0,
                )

        return sorted(matches.values(), key=lambda item: item.name.casefold())
