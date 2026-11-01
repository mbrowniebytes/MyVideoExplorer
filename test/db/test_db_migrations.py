import shutil
from pathlib import Path

import duckdb

from MyVideoExplorer.db.db_migrations import DbMigrations

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = PROJECT_ROOT / "src" / "MyVideoExplorer" / "db" / "migrations"


def test_run_migrations_on_fresh_install(tmp_path):
    db_path = tmp_path / "fresh_install.db"
    migration = DbMigrations(str(db_path))
    migration.migrations_dir = MIGRATIONS_DIR

    migration.run_migrations()

    assert db_path.exists()

    con = duckdb.connect(str(db_path))
    tables = {
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    }

    assert {"schema_migrations", "media_file", "media_path_stats"}.issubset(tables)
    assert con.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall() == [
        ("20260801_create_media.sql",),
        ("20260803_add_play_history.sql",),
        ("20260930_add_user_tags.sql",),
        ("20261027_normalize_posix_paths.sql",),
    ]
    columns = {
        row[0]
        for row in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'media_file'"
        ).fetchall()
    }
    assert {"qty_played", "last_played", "user_tags"}.issubset(columns)
    con.close()


def test_posix_path_migration_merges_colliding_legacy_rows(tmp_path):
    db_path = tmp_path / "legacy_paths.db"
    DbMigrations.clear_migrated_cache()
    migration = DbMigrations(str(db_path))
    migration.migrations_dir = MIGRATIONS_DIR
    migration.run_migrations()

    with duckdb.connect(str(db_path)) as con:
        con.execute(
            "INSERT INTO media_file (media_path, file_path, title, user_tags, qty_played) "
            "VALUES (?, ?, ?, ?, ?), (?, ?, ?, ?, ?)",
            (
                "\\media",
                "\\media\\film.mkv",
                "Legacy title",
                ["legacy"],
                7,
                "/media",
                "/media/film.mkv",
                "POSIX title",
                ["posix"],
                3,
            ),
        )
        con.execute(
            "INSERT INTO media_path_stats (media_path, files_count, last_scanned) "
            "VALUES (?, ?, ?), (?, ?, ?)",
            (
                "\\media",
                1,
                "2024-01-01 00:00:00+00",
                "/media",
                2,
                "2025-01-01 00:00:00+00",
            ),
        )
        con.execute(
            "DELETE FROM schema_migrations WHERE version = ?",
            ("20261027_normalize_posix_paths.sql",),
        )

    DbMigrations.clear_migrated_cache()
    migration.run_migrations()

    with duckdb.connect(str(db_path)) as con:
        media_rows = con.execute(
            "SELECT media_path, file_path, title, user_tags, qty_played FROM media_file"
        ).fetchall()
        stats_rows = con.execute(
            "SELECT media_path, files_count FROM media_path_stats"
        ).fetchall()
    assert media_rows == [
        ("/media", "/media/film.mkv", "POSIX title", ["posix", "legacy"], 7)
    ]
    assert stats_rows == [("/media", 2)]


def test_run_migrations_on_upgrade(tmp_path):
    db_path = tmp_path / "upgrade.db"
    con = duckdb.connect(str(db_path))
    con.execute(
        (MIGRATIONS_DIR / "20260801_create_media.sql").read_text(encoding="utf-8")
    )
    con.execute(
        "INSERT INTO schema_migrations (version) VALUES (?)",
        ("20260801_create_media.sql",),
    )
    con.close()

    migration_dir = tmp_path / "migrations"
    migration_dir.mkdir()
    shutil.copy2(
        MIGRATIONS_DIR / "20260801_create_media.sql",
        migration_dir / "20260801_create_media.sql",
    )
    shutil.copy2(
        MIGRATIONS_DIR / "20260803_add_play_history.sql",
        migration_dir / "20260803_add_play_history.sql",
    )
    shutil.copy2(
        MIGRATIONS_DIR / "20260930_add_user_tags.sql",
        migration_dir / "20260930_add_user_tags.sql",
    )
    (migration_dir / "20260802_add_upgrade_marker.sql").write_text(
        "CREATE TABLE IF NOT EXISTS media_upgrade_marker (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )

    migration = DbMigrations(str(db_path))
    migration.migrations_dir = migration_dir

    migration.run_migrations()

    con = duckdb.connect(str(db_path))
    applied_versions = con.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall()
    assert applied_versions == [
        ("20260801_create_media.sql",),
        ("20260802_add_upgrade_marker.sql",),
        ("20260803_add_play_history.sql",),
        ("20260930_add_user_tags.sql",),
    ]
    assert con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='media_upgrade_marker'"
    ).fetchone() == ("media_upgrade_marker",)
    con.close()
