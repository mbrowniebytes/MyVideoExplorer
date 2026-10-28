from pathlib import Path

import duckdb

from MyVideoExplorer.utils.file_util import FileUtils

POSIX_PATH_MIGRATION = "20261027_normalize_posix_paths.sql"


class DbMigrations:
    _migrated_dbs: set[str] = set()

    def __init__(self, db_path: str):
        self.db_path = FileUtils.normalize_path(db_path)
        self.migrations_dir = Path(__file__).parent / "migrations"

    @classmethod
    def clear_migrated_cache(cls) -> None:
        cls._migrated_dbs.clear()

    def run_migrations(self):
        if not str(self.db_path).strip():
            raise ValueError("Database path is empty. A valid media name is required.")

        resolved_path = FileUtils.resolve_path(self.db_path)
        if resolved_path in self._migrated_dbs:
            return

        db_dir = Path(self.db_path).parent
        if db_dir != Path():
            db_dir.mkdir(parents=True, exist_ok=True)

        con = duckdb.connect(self.db_path)
        try:
            # Check if schema_migrations table exists
            table_exists = False
            try:
                res = con.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = 'schema_migrations'"
                ).fetchone()
                if res:
                    table_exists = True
            except Exception:
                pass

            applied = []
            if table_exists:
                applied = [
                    row[0]
                    for row in con.execute(
                        "SELECT version FROM schema_migrations"
                    ).fetchall()
                ]

            # Get available migrations
            migration_files = sorted(
                path.name
                for path in self.migrations_dir.iterdir()
                if path.suffix == ".sql"
            )

            for migration_file in migration_files:
                if migration_file not in applied:
                    print(f"Applying migration: {migration_file}")
                    migration_path = self.migrations_dir / migration_file
                    with migration_path.open(encoding="utf-8") as f:
                        sql = f.read()
                        if migration_file == POSIX_PATH_MIGRATION:
                            self._normalize_legacy_paths(con)
                        con.execute(sql)

                        con.execute(
                            "INSERT INTO schema_migrations (version) VALUES (?)",
                            (migration_file,),
                        )
            self._migrated_dbs.add(resolved_path)
        finally:
            con.close()

    @staticmethod
    def _normalize_legacy_paths(con: duckdb.DuckDBPyConnection) -> None:
        """Normalize old separator styles while preserving rows that collide."""
        con.begin()
        try:
            columns = [
                column[0]
                for column in con.execute(
                    "SELECT * FROM media_file LIMIT 0"
                ).description
            ]
            con.execute(
                "UPDATE media_file SET media_path = replace(media_path, chr(92), '/') "
                "WHERE media_path IS NOT NULL"
            )
            rows = [
                dict(zip(columns, row, strict=True))
                for row in con.execute("SELECT * FROM media_file").fetchall()
            ]
            groups: dict[str, list[dict]] = {}
            for row in rows:
                file_path = row.get("file_path")
                if file_path:
                    key = FileUtils.normalize_path(file_path)
                    groups.setdefault(key, []).append(row)

            array_columns = {"tags", "genres", "actors", "directors", "user_tags"}
            for normalized_path, grouped_rows in groups.items():
                winner = max(
                    grouped_rows,
                    key=lambda row: (
                        row["file_path"] == normalized_path,
                        -(row.get("id") or 0),
                    ),
                )
                merged = dict(winner)
                for row in grouped_rows:
                    if row is winner:
                        continue
                    for column in columns:
                        value = row.get(column)
                        if column in {"id", "file_path"} or value is None:
                            continue
                        if column == "media_path":
                            if merged.get(column) is None:
                                merged[column] = FileUtils.normalize_path(value)
                            continue
                        if column in array_columns:
                            values = list(merged.get(column) or [])
                            for item in value or []:
                                if item not in values:
                                    values.append(item)
                            merged[column] = values
                        elif column == "qty_played":
                            merged[column] = max(merged.get(column) or 0, value)
                        elif column in {"created_at", "modified_at", "last_played"}:
                            current = merged.get(column)
                            if (
                                current is None
                                or (column != "created_at" and value > current)
                                or (column == "created_at" and value < current)
                            ):
                                merged[column] = value
                        elif merged.get(column) is None:
                            merged[column] = value

                merged["file_path"] = normalized_path
                if merged.get("media_path"):
                    merged["media_path"] = FileUtils.normalize_path(
                        merged["media_path"]
                    )

                duplicate_ids = [
                    row["id"] for row in grouped_rows if row["id"] != winner["id"]
                ]
                if duplicate_ids:
                    con.execute(
                        "DELETE FROM media_file WHERE id IN (SELECT unnest(?))",
                        (duplicate_ids,),
                    )

                update_columns = [column for column in columns if column != "id"]
                assignments = ", ".join(f'"{column}" = ?' for column in update_columns)
                con.execute(
                    f"UPDATE media_file SET {assignments} WHERE id = ?",
                    [merged.get(column) for column in update_columns] + [winner["id"]],
                )

            stats = con.execute(
                "SELECT media_path, subfolders_count, files_count, images_count, "
                "videos_count, nfo_count, other_count, last_scanned "
                "FROM media_path_stats"
            ).fetchall()
            stats_groups: dict[str, list[tuple]] = {}
            for row in stats:
                if row[0]:
                    stats_groups.setdefault(
                        FileUtils.normalize_path(row[0]), []
                    ).append(row)
            for normalized_path, grouped_rows in stats_groups.items():
                winner = max(
                    grouped_rows,
                    key=lambda row: (row[7] is not None, row[7]),
                )
                con.execute(
                    "DELETE FROM media_path_stats WHERE media_path IN (SELECT unnest(?))",
                    ([row[0] for row in grouped_rows],),
                )
                con.execute(
                    "INSERT INTO media_path_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (normalized_path, *winner[1:]),
                )
            con.commit()
        except Exception:
            con.rollback()
            raise
