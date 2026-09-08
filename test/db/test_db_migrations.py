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
    assert con.execute("SELECT version FROM schema_migrations").fetchall() == [
        ("20260801_create_media.sql",)
    ]
    con.close()


def test_run_migrations_on_upgrade(tmp_path):
    db_path = tmp_path / "upgrade.db"
    con = duckdb.connect(str(db_path))
    con.execute(
        "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )
    con.execute("INSERT INTO schema_migrations (version) VALUES (?)", ("20260801_create_media.sql",))
    con.close()

    migration_dir = tmp_path / "migrations"
    migration_dir.mkdir()
    shutil.copy2(MIGRATIONS_DIR / "20260801_create_media.sql", migration_dir / "20260801_create_media.sql")
    (migration_dir / "20260802_add_upgrade_marker.sql").write_text(
        "CREATE TABLE IF NOT EXISTS media_upgrade_marker (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )

    migration = DbMigrations(str(db_path))
    migration.migrations_dir = migration_dir

    migration.run_migrations()

    con = duckdb.connect(str(db_path))
    applied_versions = con.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    assert applied_versions == [
        ("20260801_create_media.sql",),
        ("20260802_add_upgrade_marker.sql",),
    ]
    assert con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='media_upgrade_marker'"
    ).fetchone() == ("media_upgrade_marker",)
    con.close()
