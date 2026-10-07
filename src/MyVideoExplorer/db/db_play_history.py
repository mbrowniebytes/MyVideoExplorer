from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.models.play_history import PlayHistory


class DbPlayHistory:
    def __init__(self, settings_state: Any) -> None:
        self.settings_state = settings_state

    def get_history(self, file_path: str) -> PlayHistory | None:
        db_path = self._get_db_path(file_path)
        if db_path is None or not Path(db_path).exists():
            return None

        DbMigrations(db_path).run_migrations()
        with duckdb.connect(db_path) as con:
            result = con.execute(
                "SELECT qty_played, last_played FROM media_file WHERE file_path = ?",
                (Path(file_path).as_posix(),),
            ).fetchone()

        if result is None:
            return None
        return PlayHistory(qty_played=result[0], last_played=result[1])

    def record_playback(self, file_path: str) -> bool:
        return self._update(
            file_path,
            "UPDATE media_file SET qty_played = qty_played + 1, "
            "last_played = CURRENT_DATE WHERE file_path = ? RETURNING file_path",
            (Path(file_path).as_posix(),),
        )

    def set_qty_played(self, file_path: str, qty_played: int) -> bool:
        return self._update(
            file_path,
            "UPDATE media_file SET qty_played = ? WHERE file_path = ? "
            "RETURNING file_path",
            (qty_played, Path(file_path).as_posix()),
        )

    def set_last_played(self, file_path: str, last_played: date | None) -> bool:
        return self._update(
            file_path,
            "UPDATE media_file SET last_played = ? WHERE file_path = ? "
            "RETURNING file_path",
            (last_played, Path(file_path).as_posix()),
        )

    def _update(self, file_path: str, query: str, parameters: tuple) -> bool:
        db_path = self._get_db_path(file_path)
        if db_path is None or not Path(db_path).exists():
            return False

        DbMigrations(db_path).run_migrations()
        with duckdb.connect(db_path) as con:
            con.begin()
            try:
                updated = con.execute(query, parameters).fetchone()
                con.commit()
            except Exception:
                con.rollback()
                raise

        return updated is not None

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
