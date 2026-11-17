from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import duckdb

from MyVideoExplorer.db.db_snowflake_id import SnowflakeIdGenerator
from MyVideoExplorer.utils.file_util import FileUtils

DbType = Literal["media", "filter_catalog", "tag_catalog"]


class DbMigrations:
    _migrated_dbs: set[str] = set()

    def __init__(self, db_path: str, db_type: DbType = "media"):
        self.db_path = FileUtils.normalize_path(db_path)
        self.db_type = db_type
        self.migrations_dir = Path(__file__).parent / "migrations"

    @classmethod
    def clear_migrated_cache(cls) -> None:
        cls._migrated_dbs.clear()

    _HEADER_START_RE = re.compile(r"^--\s*@migration\s*$")
    _HEADER_FIELD_RE = re.compile(r"^--\s+(\w+):\s*(.*)$")

    @staticmethod
    def _parse_migration_header(migration_path: Path) -> dict | None:
        """Parse the Liquibase-style multiline header from a migration SQL file.

        Expects a block like:
            -- @migration
            -- db: media
            -- purpose: Recreate media_file with BIGINT PK
            -- python_pre_step: reassign_snowflake_ids

        Returns a dict with keys 'db', 'purpose', and optionally 'python_pre_step',
        or None if the header is missing or invalid.
        """
        try:
            text = migration_path.read_text(encoding="utf-8")
        except OSError:
            return None

        header: dict[str, str] = {}
        in_header = False
        for line in text.splitlines():
            stripped = line.strip()
            if not in_header:
                if DbMigrations._HEADER_START_RE.match(stripped):
                    in_header = True
                continue
            # Inside the header block: read consecutive -- lines
            if not stripped.startswith("--"):
                break  # end of comment block
            m = DbMigrations._HEADER_FIELD_RE.match(stripped)
            if m:
                header[m.group(1)] = m.group(2).strip()
            elif stripped == "--":
                break
        return header if "db" in header and "purpose" in header else None

    def _is_migration_for_type(self, migration_path: Path) -> bool:
        header = self._parse_migration_header(migration_path)
        if header is None:
            return False
        return header.get("db") == self.db_type

    @staticmethod
    def _get_python_pre_step(header: dict | None) -> str | None:
        """Extract the python_pre_step name from a migration header, if present."""
        if header is None:
            return None
        return header.get("python_pre_step")

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

            # Get available migrations (filter by header comment for target db)
            migration_files = sorted(
                path
                for path in self.migrations_dir.iterdir()
                if path.suffix == ".sql" and self._is_migration_for_type(path)
            )

            # Map python_pre_step names to bound methods
            _pre_step_dispatch: dict[str, object] = {
                "normalize_legacy_paths": self._normalize_legacy_paths,
                "reassign_snowflake_ids": self._reassign_to_snowflake_ids,
                "reassign_filter_to_snowflake_ids": self._reassign_filter_to_snowflake_ids,
            }

            for migration_path in migration_files:
                migration_file = migration_path.name
                if migration_file not in applied:
                    print(f"Applying migration: {migration_file}")
                    header = self._parse_migration_header(migration_path)
                    pre_step_name = self._get_python_pre_step(header)
                    if pre_step_name is not None:
                        method = _pre_step_dispatch.get(pre_step_name)
                        if method is not None:
                            method(con)
                        else:
                            print(
                                f"Warning: Unknown python_pre_step '{pre_step_name}' "
                                f"in migration {migration_file}"
                            )
                    with migration_path.open(encoding="utf-8") as f:
                        sql = f.read()
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

    @staticmethod
    def _reassign_to_snowflake_ids(con: duckdb.DuckDBPyConnection) -> None:
        """Build an ID mapping table so the SQL migration can assign snowflake IDs.

        We cannot UPDATE the old INTEGER column with BIGINT snowflake values —
        the destination type overflows.  Instead we populate _id_mapping and let
        the SQL migration (20261101_snowflake_ids.sql) join against it when
        copying rows into the new BIGINT table.
        """
        con.begin()
        try:
            con.execute(
                "CREATE TABLE IF NOT EXISTS _id_mapping "
                "(old_id BIGINT PRIMARY KEY, new_id BIGINT)"
            )
            con.execute("DELETE FROM _id_mapping")
            rows = con.execute(
                "SELECT id FROM media_file WHERE id IS NOT NULL"
            ).fetchall()
            if not rows:
                con.commit()
                return
            generator = SnowflakeIdGenerator()
            for (old_id,) in rows:
                new_id = generator.generate()
                con.execute(
                    "INSERT INTO _id_mapping (old_id, new_id) VALUES (?, ?)",
                    (old_id, new_id),
                )
            con.commit()
        except Exception:
            con.rollback()
            raise

    @staticmethod
    def _reassign_filter_to_snowflake_ids(con: duckdb.DuckDBPyConnection) -> None:
        """Reassign existing media_filters filter_id values to snowflake BIGINT IDs.

        This runs before the SQL migration that recreates the table with BIGINT PK,
        so the placeholder 0 values in the SQL are replaced with real snowflake IDs.
        """
        con.begin()
        try:
            # Always create the mapping table so the SQL migration can reference it
            con.execute(
                "CREATE TABLE IF NOT EXISTS _filter_id_mapping "
                "(name TEXT PRIMARY KEY, new_id BIGINT)"
            )
            con.execute("DELETE FROM _filter_id_mapping")
            rows = con.execute("SELECT name FROM media_filters").fetchall()
            if not rows:
                con.commit()
                return
            generator = SnowflakeIdGenerator()
            for (name,) in rows:
                new_id = generator.generate()
                con.execute(
                    "INSERT INTO _filter_id_mapping (name, new_id) VALUES (?, ?)",
                    (name, new_id),
                )
            con.commit()
        except Exception:
            con.rollback()
            raise
