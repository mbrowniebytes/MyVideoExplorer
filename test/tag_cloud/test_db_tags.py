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
