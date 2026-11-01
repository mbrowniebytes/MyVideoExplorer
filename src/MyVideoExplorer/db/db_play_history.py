from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.models.play_history import PlayHistory
from MyVideoExplorer.utils.file_util import FileUtils


class DbPlayHistory:
    def __init__(
        self, settings_state: Any, path_utils: FileUtils | None = None
    ) -> None:
        self.settings_state = settings_state
        self.path_utils = path_utils or FileUtils()

    def get_history(self, file_path: str) -> PlayHistory | None:
        db_path = self._get_db_path(file_path)
        if (
            db_path is None
            or not Path(self.path_utils.normalize_path(db_path)).exists()
        ):
            return None

        DbMigrations(db_path).run_migrations()
        posix_path = self.path_utils.normalize_path(file_path)
        with duckdb.connect(self.path_utils.normalize_path(db_path)) as con:
            result = con.execute(
                "SELECT qty_played, last_played FROM media_file "
                "WHERE file_path = ? OR lower(file_path) = lower(?)",
                (posix_path, posix_path),
            ).fetchone()

        if result is None:
            return None
        return PlayHistory(qty_played=result[0], last_played=result[1])

    def record_playback(self, file_path: str) -> bool:
        posix_path = self.path_utils.normalize_path(file_path)
        return self._update(
            file_path,
            "UPDATE media_file SET qty_played = qty_played + 1, "
            "last_played = CURRENT_DATE WHERE file_path = ? OR lower(file_path) = lower(?) "
            "RETURNING file_path",
            (posix_path, posix_path),
        )

    def set_qty_played(self, file_path: str, qty_played: int) -> bool:
        posix_path = self.path_utils.normalize_path(file_path)
        return self._update(
            file_path,
            "UPDATE media_file SET qty_played = ? WHERE file_path = ? OR lower(file_path) = lower(?) "
            "RETURNING file_path",
            (qty_played, posix_path, posix_path),
        )

    def set_last_played(self, file_path: str, last_played: date | None) -> bool:
        posix_path = self.path_utils.normalize_path(file_path)
        return self._update(
            file_path,
            "UPDATE media_file SET last_played = ? WHERE file_path = ? OR lower(file_path) = lower(?) "
            "RETURNING file_path",
            (last_played, posix_path, posix_path),
        )

    def _update(self, file_path: str, query: str, parameters: tuple) -> bool:
        db_path = self._get_db_path(file_path)
        if (
            db_path is None
            or not Path(self.path_utils.normalize_path(db_path)).exists()
        ):
            return False

        DbMigrations(db_path).run_migrations()
        with duckdb.connect(self.path_utils.normalize_path(db_path)) as con:
            con.begin()
            try:
                updated = con.execute(query, parameters).fetchone()
                con.commit()
            except Exception:
                con.rollback()
                raise

        return updated is not None

    def _get_db_path(self, file_path: str) -> str | None:
        target_path = self.path_utils.resolve_path(file_path)
        matching_configs: list[tuple[int, dict[str, Any]]] = []
        for config in self.settings_state.media_configs:
            configured_path = str(config.get("path", "")).strip()
            if not configured_path:
                continue
            root_path = self.path_utils.resolve_path(configured_path)
            if not self.path_utils.is_same_or_descendant(target_path, root_path):
                continue
            matching_configs.append((self.path_utils.depth(root_path), config))

        if not matching_configs:
            return None
        config = max(matching_configs, key=lambda item: item[0])[1]
        return self.settings_state.get_db_path(config)
