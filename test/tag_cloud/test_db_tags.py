import duckdb

from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.settings.settings_state import SettingsState


class MockTagState:
    tags: list[dict[str, str]] = []
    json_util = type("Json", (), {"load_json": staticmethod(lambda _path: {})})()
    normalize_tags = staticmethod(SettingsState.normalize_tags)

    def __init__(self, media_configs, db_paths):
        self.media_configs = media_configs
        self.db_paths = db_paths

    def get_db_path(self, config):
        return self.db_paths[config["path"]]

    def set_tags(self, tags):
        self.tags = tags


def test_media_tags_and_catalog_counts_across_media_databases(tmp_path):
    media_root = tmp_path / "media"
    media_root.mkdir()
    file_path = media_root / "film.mkv"
    file_path.touch()
    db_path = tmp_path / "media.db"
    DbMigrations(str(db_path)).run_migrations()
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            "INSERT INTO media_file (file_path, user_tags) VALUES (?, ?)",
            (file_path.as_posix(), []),
        )

    second_root = tmp_path / "second_media"
    second_root.mkdir()
    second_file = second_root / "second_film.mkv"
    second_file.touch()
    second_db_path = tmp_path / "second_media.db"
    DbMigrations(str(second_db_path)).run_migrations()
    with duckdb.connect(str(second_db_path)) as con:
        con.execute(
            "INSERT INTO media_file (file_path, user_tags) VALUES (?, ?)",
            (second_file.as_posix(), ["Favorite"]),
        )

    state = MockTagState(
        [
            {"path": str(media_root)},
            {"path": str(second_root)},
        ],
        {
            str(media_root): str(db_path),
            str(second_root): str(second_db_path),
        },
    )
    tags = DbTags(state, tmp_path / "tag_catalog.db")
    assert tags.add_catalog_tag("Favorite", "#ff0000")
    assert tags.set_tag_color("Favorite", "#112233")
    assert tags.list_tags() == [{"tag": "Favorite", "color": "#112233"}]

    assert tags.get_tags(str(file_path)) == []
    assert tags.set_tags(str(file_path), ["Favorite", "Rewatch"])
    assert tags.get_tags(str(file_path)) == ["Favorite", "Rewatch"]
    assert tags.get_tag_counts() == {"favorite": 2, "rewatch": 1}

    tags.replace_catalog(
        [{"tag": "Loved", "color": "#ff0000"}],
        {"Favorite": "Loved"},
        ["Rewatch"],
    )
    assert tags.get_tags(str(file_path)) == ["Loved"]
    assert tags.get_tags(str(second_file)) == ["Loved"]
    assert tags.get_tag_counts() == {"loved": 2}

    assert tags.update_catalog_tag("Loved", "Rewatch", "#123456")
    assert tags.list_tags() == [{"tag": "Rewatch", "color": "#123456"}]
    assert tags.get_tags(str(file_path)) == ["Rewatch"]
    assert tags.get_tags(str(second_file)) == ["Rewatch"]


def test_db_tags_caching_and_invalidation(tmp_path):
    media_root = tmp_path / "media"
    media_root.mkdir()
    file_path = media_root / "sample.mp4"
    file_path.touch()
    db_path = tmp_path / "media.db"
    DbMigrations(str(db_path)).run_migrations()
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            "INSERT INTO media_file (file_path, user_tags) VALUES (?, ?)",
            (file_path.as_posix(), []),
        )

    state = MockTagState(
        [{"path": str(media_root)}],
        {str(media_root): str(db_path)},
    )
    tags = DbTags(state, tmp_path / "tag_catalog.db")
    tags.add_catalog_tag("Action", "#ff0000")

    # Catalog cache
    listed = tags.list_tags()
    assert listed == [{"tag": "Action", "color": "#ff0000"}]
    assert tags._tags_cache is not None

    # Counts cache
    counts1 = tags.get_tag_counts()
    assert counts1 == {}
    assert tags._tag_counts_cache == {}

    # Updating tags invalidates counts cache
    tags.set_tags(str(file_path), ["Action"])
    assert tags._tag_counts_cache is None
    counts2 = tags.get_tag_counts()
    assert counts2 == {"action": 1}
    assert tags._tag_counts_cache == {"action": 1}

    # Updating color updates catalog and repopulates state
    tags.set_tag_color("Action", "#00ff00")
    assert tags.list_tags() == [{"tag": "Action", "color": "#00ff00"}]
    assert tags._tags_cache == [{"tag": "Action", "color": "#00ff00"}]


def test_db_migrations_cache(tmp_path):
    DbMigrations.clear_migrated_cache()
    db_path = str(tmp_path / "migrated.db")
    migration = DbMigrations(db_path)
    migration.run_migrations()
    assert str((tmp_path / "migrated.db").resolve()) in DbMigrations._migrated_dbs

    # Calling run_migrations again returns early
    migration.run_migrations()
    DbMigrations.clear_migrated_cache()
    assert len(DbMigrations._migrated_dbs) == 0
