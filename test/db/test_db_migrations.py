import shutil
from pathlib import Path
from types import SimpleNamespace

import duckdb

from MyVideoExplorer.db.db_filters import DbFilters
from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.db_snowflake_id import SnowflakeIdGenerator

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
        ("20261101_snowflake_ids.sql",),
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
        gen = SnowflakeIdGenerator()
        con.execute(
            "INSERT INTO media_file (id, media_path, file_path, title, user_tags, qty_played) "
            "VALUES (?, ?, ?, ?, ?, ?), (?, ?, ?, ?, ?, ?)",
            (
                gen.generate(),
                "\\media",
                "\\media\\film.mkv",
                "Legacy title",
                ["legacy"],
                7,
                gen.generate(),
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


def test_snowflake_migration_converts_integer_ids(tmp_path):
    """Verify that the snowflake migration works when media_file.id is INTEGER.

    Older databases used INTEGER + SEQUENCE for auto-increment IDs.  The
    snowflake migration must convert these to BIGINT snowflake values without
    overflowing the INTEGER column during the transition.
    """
    db_path = tmp_path / "integer_ids.db"
    con = duckdb.connect(str(db_path))
    # Create the old-style schema with INTEGER + SEQUENCE
    con.execute("CREATE SEQUENCE media_id_seq START 1;")
    con.execute(
        "CREATE TABLE media_file ("
        "id INTEGER PRIMARY KEY DEFAULT nextval('media_id_seq'),"
        "media_path TEXT, file_path TEXT, type TEXT, title TEXT,"
        "year SMALLINT, plot TEXT, score DECIMAL(4,2), rated TEXT,"
        "runtime SMALLINT, tags VARCHAR[], genres VARCHAR[],"
        "actors VARCHAR[], directors VARCHAR[],"
        "qty_played INTEGER DEFAULT 0, last_played DATE,"
        "user_tags VARCHAR[] DEFAULT [],"
        "created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,"
        "modified_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP"
        ");"
    )
    con.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_file_path ON media_file(file_path);"
    )
    con.execute(
        "CREATE TABLE media_path_stats ("
        "media_path TEXT PRIMARY KEY, subfolders_count INTEGER,"
        "files_count INTEGER, images_count INTEGER, videos_count INTEGER,"
        "nfo_count INTEGER, other_count INTEGER, last_scanned TIMESTAMPTZ"
        ");"
    )
    con.execute(
        "CREATE TABLE schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP"
        ");"
    )
    # Mark earlier migrations as applied
    con.execute(
        "INSERT INTO schema_migrations (version) VALUES (?), (?), (?), (?)",
        (
            "20260801_create_media.sql",
            "20260803_add_play_history.sql",
            "20260930_add_user_tags.sql",
            "20261027_normalize_posix_paths.sql",
        ),
    )
    # Insert rows with auto-increment INTEGER IDs
    con.execute(
        "INSERT INTO media_file (media_path, file_path, title) VALUES "
        "('/test', '/test/a.mp4', 'Movie A'), "
        "('/test', '/test/b.mp4', 'Movie B'), "
        "('/test', '/test/c.mp4', 'Movie C')"
    )
    old_ids = [
        row[0]
        for row in con.execute("SELECT id FROM media_file ORDER BY id").fetchall()
    ]
    assert old_ids == [1, 2, 3], f"Expected [1, 2, 3], got {old_ids}"
    con.close()

    # Run migrations — the snowflake migration should convert INTEGER to BIGINT
    DbMigrations.clear_migrated_cache()
    migration = DbMigrations(str(db_path))
    migration.migrations_dir = MIGRATIONS_DIR
    migration.run_migrations()

    # Verify the result
    con = duckdb.connect(str(db_path))
    col_type_row = con.execute(
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name='media_file' AND column_name='id'"
    ).fetchone()
    assert col_type_row is not None and col_type_row[0] == "BIGINT", (
        f"Expected BIGINT, got {col_type_row}"
    )

    new_ids = [
        row[0]
        for row in con.execute("SELECT id FROM media_file ORDER BY id").fetchall()
    ]
    assert len(new_ids) == 3
    # All IDs should be snowflake values (> 1 trillion)
    for id_val in new_ids:
        assert id_val > 1_000_000_000_000, f"ID {id_val} is not a snowflake value"
    # IDs should be different from old sequential IDs
    assert new_ids != old_ids, "IDs were not converted to snowflake values"

    # Verify data integrity — titles should be preserved
    titles = [
        row[0]
        for row in con.execute("SELECT title FROM media_file ORDER BY id").fetchall()
    ]
    assert titles == ["Movie A", "Movie B", "Movie C"]

    # Verify the migration is recorded
    applied = [
        row[0]
        for row in con.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    ]
    assert "20261101_snowflake_ids.sql" in applied

    # Verify _id_mapping cleanup table is gone
    mapping_exists = con.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name='_id_mapping'"
    ).fetchone()
    assert mapping_exists is None, "_id_mapping table should be dropped after migration"

    con.close()


def _create_manual_filter_store(tmp_path: Path) -> DbFilters:
    media_db = tmp_path / "manual_media.db"
    DbMigrations(str(media_db)).run_migrations()
    with duckdb.connect(media_db.as_posix()) as con:
        con.executemany(
            """
            INSERT INTO media_file
                (id, media_path, file_path, type, title, qty_played)
            VALUES (?, '/media/a', ?, 'video', ?, ?)
            """,
            [
                (101, "/media/a/Group/Alpha.mp4", "Alpha", 2),
                (102, "/media/a/Group/Beta.mp4", "Beta", 9),
            ],
        )
    settings = SimpleNamespace(
        media_configs=[{"path": "/media/a", "db": media_db.as_posix()}],
        get_db_path=lambda config: config["db"],
    )
    return DbFilters(settings, tmp_path / "manual_filters.db")


def test_filter_catalog_upgrade_adds_manual_sort_fields(tmp_path):
    db_path = tmp_path / "existing_filters.db"
    with duckdb.connect(db_path.as_posix()) as con:
        con.execute(
            "CREATE TABLE schema_migrations "
            "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)"
        )
        con.executemany(
            "INSERT INTO schema_migrations (version) VALUES (?)",
            [
                ("20261101_create_filter_catalog.sql",),
                ("20261102_filter_snowflake_ids.sql",),
            ],
        )
        con.execute(
            """
            CREATE TABLE media_filters (
                filter_id BIGINT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                criteria JSON NOT NULL,
                folder_counts MAP(VARCHAR, BIGINT) NOT NULL,
                total_count BIGINT,
                sort_order INTEGER NOT NULL
            )
            """
        )
        con.execute(
            """
            INSERT INTO media_filters
            VALUES (1, 'Existing', '[]'::JSON, map([]::VARCHAR[], []::BIGINT[]), NULL, 0)
            """
        )

    store = DbFilters(SimpleNamespace(media_configs=[]), db_path)

    assert store.get_filter("Existing") == {
        "name": "Existing",
        "filters": [],
        "folder_counts": {},
        "total_count": None,
        "sort_option": "default",
        "needs_rebuild": False,
    }


def test_manual_refresh_preserves_order_appends_matches_and_reindexes(tmp_path):
    store = _create_manual_filter_store(tmp_path)
    store.save_filter(
        "Playlist",
        [],
        sort_option="manual",
        manual_items=[
            {
                "media_folder": "/media/a",
                "media_id": 102,
                "rel_path": "Group/Beta.mp4",
            }
        ],
    )

    store.refresh_filter("Playlist")

    assert [item["media_id"] for item in store.get_manual_items("Playlist")] == [
        102,
        101,
    ]
    with duckdb.connect(store.path_utils.normalize_path(store.db_path)) as con:
        assert con.execute(
            "SELECT order_index FROM filter_manual_list ORDER BY order_index"
        ).fetchall() == [(1,), (2,)]


def test_scan_marks_stale_items_without_relinking_and_refresh_removes_them(tmp_path):
    store = _create_manual_filter_store(tmp_path)
    store.save_filter(
        "Playlist",
        [],
        sort_option="manual",
        manual_items=[
            {
                "media_folder": "/media/a",
                "media_id": 101,
                "rel_path": "Group/Alpha.mp4",
            }
        ],
    )
    media_db = store.settings_state.media_configs[0]["db"]
    with duckdb.connect(media_db) as con:
        con.execute("UPDATE media_file SET id = 103 WHERE id = 101")

    assert store.mark_manual_items_stale("/media/a") == ["Playlist"]
    assert store.get_manual_items("Playlist")[0]["status"] == "missing"
    assert store.get_filter("Playlist")["needs_rebuild"] is True

    store.refresh_filter("Playlist")

    assert [
        (item["media_id"], item["status"])
        for item in store.get_manual_items("Playlist")
    ] == [
        (103, "exists"),
        (102, "exists"),
    ]
    assert store.get_filter("Playlist")["needs_rebuild"] is False


def test_live_sort_and_nonmanual_refresh_do_not_rewrite_manual_rows(tmp_path):
    store = _create_manual_filter_store(tmp_path)
    results = store.db_filter.matching_videos([], sort_option="qty_played")
    assert [item["media_id"] for item in results] == [102, 101]

    store.save_filter(
        "Live",
        [],
        sort_option="manual",
        manual_items=[
            {
                "media_folder": "/media/a",
                "media_id": 102,
                "rel_path": "Group/Beta.mp4",
            }
        ],
    )
    store.save_filter("Live", [], original_name="Live", sort_option="a_z")
    before = store.get_manual_items("Live")

    store.refresh_filter("Live")

    assert store.get_filter("Live")["sort_option"] == "a_z"
    assert store.get_manual_items("Live") == before


def test_metadata_sorts_use_title_ascending_as_tie_breaker(tmp_path):
    store = _create_manual_filter_store(tmp_path)
    media_db = store.settings_state.media_configs[0]["db"]
    with duckdb.connect(media_db) as con:
        con.execute(
            """
            UPDATE media_file
            SET title = CASE id WHEN 101 THEN 'Zulu' ELSE 'Aardvark' END,
                qty_played = 5,
                last_played = DATE '2026-11-03'
            """
        )

    for sort_option in ("last_played", "qty_played"):
        results = store.db_filter.matching_videos([], sort_option=sort_option)
        assert [item["title"] for item in results] == ["Aardvark", "Zulu"]
