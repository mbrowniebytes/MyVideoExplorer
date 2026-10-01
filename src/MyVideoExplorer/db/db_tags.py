from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.db.db_migrations import DbMigrations

DEFAULT_TAG_DB_PATH = Path("db") / "tag_catalog.db"


class DbTags:
    def __init__(
        self,
        settings_state: Any,
        db_path: Path | str = DEFAULT_TAG_DB_PATH,
    ) -> None:
        self.settings_state = settings_state
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.db_path)) as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    tag TEXT PRIMARY KEY,
                    color TEXT NOT NULL DEFAULT '#808080'
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS tag_catalog_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            imported = con.execute(
                "SELECT value FROM tag_catalog_meta "
                "WHERE key = 'legacy_settings_tags_imported'"
            ).fetchone()
            if imported is None:
                legacy_tags = settings_state.normalize_tags(
                    settings_state.json_util.load_json(
                        Path("cfg") / "settings_tags.json"
                    ).get("tags", [])
                )
                if isinstance(legacy_tags, list) and legacy_tags:
                    con.executemany(
                        "INSERT INTO tags (tag, color) VALUES (?, ?) "
                        "ON CONFLICT (tag) DO NOTHING",
                        [(item["tag"], item["color"]) for item in legacy_tags],
                    )
                con.execute(
                    "INSERT INTO tag_catalog_meta (key, value) "
                    "VALUES ('legacy_settings_tags_imported', 'true')"
                )
        self._sync_state()

    def list_tags(self) -> list[dict[str, str]]:
        with duckdb.connect(str(self.db_path), read_only=True) as con:
            rows = con.execute(
                "SELECT tag, color FROM tags ORDER BY lower(tag)"
            ).fetchall()
        return [{"tag": row[0], "color": row[1]} for row in rows]

    def add_catalog_tag(self, tag: str, color: str = "#808080") -> bool:
        normalized = self.settings_state.normalize_tags([{"tag": tag, "color": color}])
        if not normalized:
            return False
        tag_data = normalized[0]
        with duckdb.connect(str(self.db_path)) as con:
            exists = con.execute(
                "SELECT 1 FROM tags WHERE lower(tag) = lower(?)", (tag_data["tag"],)
            ).fetchone()
            if exists:
                return False
            con.execute(
                "INSERT INTO tags (tag, color) VALUES (?, ?)",
                (tag_data["tag"], tag_data["color"]),
            )
        self._sync_state()
        return True

    def set_tag_color(self, tag: str, color: str) -> bool:
        normalized = self.settings_state.normalize_tags([{"tag": tag, "color": color}])
        if not normalized:
            return False
        with duckdb.connect(str(self.db_path)) as con:
            updated = con.execute(
                "UPDATE tags SET color = ? WHERE lower(tag) = lower(?) RETURNING tag",
                (normalized[0]["color"], normalized[0]["tag"]),
            ).fetchone()
        if updated is None:
            return False
        self._sync_state()
        return True

    def update_catalog_tag(
        self,
        old_tag: str,
        new_tag: str,
        color: str,
    ) -> bool:
        existing_tags = self.list_tags()
        matching = next(
            (
                item
                for item in existing_tags
                if item["tag"].casefold() == old_tag.casefold()
            ),
            None,
        )
        if matching is None:
            return False
        if any(
            item["tag"].casefold() == new_tag.casefold()
            and item["tag"].casefold() != old_tag.casefold()
            for item in existing_tags
        ):
            return False

        updated_tags = [
            {
                "tag": new_tag
                if item["tag"].casefold() == old_tag.casefold()
                else item["tag"],
                "color": color
                if item["tag"].casefold() == old_tag.casefold()
                else item["color"],
            }
            for item in existing_tags
        ]
        self.replace_catalog(
            updated_tags,
            {old_tag: new_tag} if old_tag != new_tag else {},
            [],
        )
        return True

    def delete_catalog_tag(self, tag: str) -> bool:
        matching = next(
            (
                item
                for item in self.list_tags()
                if item["tag"].casefold() == tag.casefold()
            ),
            None,
        )
        if matching is None:
            return False
        remaining = [
            item
            for item in self.list_tags()
            if item["tag"].casefold() != tag.casefold()
        ]
        self.replace_catalog(remaining, {}, [matching["tag"]])
        return True

    def replace_catalog(
        self,
        tags: list[dict[str, str]],
        renamed: dict[str, str],
        deleted: list[str],
    ) -> None:
        normalized = self.settings_state.normalize_tags(tags)
        if len(normalized) != len([tag for tag in tags if tag.get("tag", "").strip()]):
            raise ValueError("Tag names must be unique and colors must be valid.")

        self._update_media_assignments(renamed, deleted)
        with duckdb.connect(str(self.db_path)) as con:
            con.begin()
            try:
                con.execute("DELETE FROM tags")
                if normalized:
                    con.executemany(
                        "INSERT INTO tags (tag, color) VALUES (?, ?)",
                        [(item["tag"], item["color"]) for item in normalized],
                    )
                con.commit()
            except Exception:
                con.rollback()
                raise
        self._sync_state()

    def get_tags(self, file_path: str) -> list[str] | None:
        db_path = self._get_db_path(file_path)
        if db_path is None or not Path(db_path).exists():
            return None

        DbMigrations(db_path).run_migrations()
        with duckdb.connect(db_path) as con:
            result = con.execute(
                "SELECT user_tags FROM media_file WHERE file_path = ?",
                (Path(file_path).as_posix(),),
            ).fetchone()

        return list(result[0] or []) if result is not None else None

    def set_tags(self, file_path: str, tags: list[str]) -> bool:
        db_path = self._get_db_path(file_path)
        if db_path is None or not Path(db_path).exists():
            return False

        DbMigrations(db_path).run_migrations()
        with duckdb.connect(db_path) as con:
            updated = con.execute(
                "UPDATE media_file SET user_tags = ? WHERE file_path = ? "
                "RETURNING file_path",
                (tags, Path(file_path).as_posix()),
            ).fetchone()
        return updated is not None

    def get_tag_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        visited_paths: set[str] = set()
        for config in self.settings_state.media_configs:
            db_path = self.settings_state.get_db_path(config)
            resolved_db_path = str(Path(db_path).resolve())
            if resolved_db_path in visited_paths or not Path(db_path).exists():
                continue
            visited_paths.add(resolved_db_path)

            DbMigrations(db_path).run_migrations()
            with duckdb.connect(db_path, read_only=True) as con:
                rows = con.execute(
                    """
                    SELECT tag, count(*)
                    FROM media_file, unnest(user_tags) AS tags(tag)
                    GROUP BY tag
                    """
                ).fetchall()
            for tag, quantity in rows:
                key = tag.casefold()
                counts[key] = counts.get(key, 0) + quantity
        return counts

    def _update_media_assignments(
        self, renamed: dict[str, str], deleted: list[str]
    ) -> None:
        rename_map = {old.casefold(): new for old, new in renamed.items()}
        deleted_tags = {tag.casefold() for tag in deleted}
        for config in self.settings_state.media_configs:
            db_path = self.settings_state.get_db_path(config)
            if not Path(db_path).exists():
                continue
            DbMigrations(db_path).run_migrations()
            with duckdb.connect(db_path) as con:
                con.begin()
                try:
                    media_rows = con.execute(
                        "SELECT file_path, user_tags FROM media_file "
                        "WHERE user_tags IS NOT NULL"
                    ).fetchall()
                    for file_path, tags in media_rows:
                        updated: list[str] = []
                        seen: set[str] = set()
                        for tag in tags or []:
                            normalized_tag = rename_map.get(tag.casefold(), tag)
                            if normalized_tag.casefold() in deleted_tags:
                                continue
                            if normalized_tag.casefold() not in seen:
                                updated.append(normalized_tag)
                                seen.add(normalized_tag.casefold())
                        if updated != list(tags or []):
                            con.execute(
                                "UPDATE media_file SET user_tags = ? "
                                "WHERE file_path = ?",
                                (updated, file_path),
                            )
                    con.commit()
                except Exception:
                    con.rollback()
                    raise

    def _sync_state(self) -> None:
        self.settings_state.set_tags(self.list_tags())

    def _get_db_path(self, file_path: str) -> str | None:
        target_path = Path(file_path).resolve()
        matching_configs: list[tuple[int, dict[str, Any]]] = []
        for config in self.settings_state.media_configs:
            configured_path = str(config.get("path", "")).strip()
            if not configured_path:
                continue
            root_path = Path(configured_path).resolve()
            try:
                target_path.relative_to(root_path)
            except ValueError:
                continue
            matching_configs.append((len(root_path.parts), config))

        if not matching_configs:
            return None
        config = max(matching_configs, key=lambda item: item[0])[1]
        return self.settings_state.get_db_path(config)
