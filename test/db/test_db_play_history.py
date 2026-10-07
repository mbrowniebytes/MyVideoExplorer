from datetime import date, datetime
from pathlib import Path

import duckdb

from MyVideoExplorer.db.db_migrations import DbMigrations
from MyVideoExplorer.db.db_play_history import DbPlayHistory
from MyVideoExplorer.db.models.media_file_metadata import MediaFileMetadata
from MyVideoExplorer.db.models.play_history import PlayHistory


class MockSettingsState:
    def __init__(self, media_root: Path, db_path: Path) -> None:
        self.media_configs = [{"label": "Movies", "path": str(media_root)}]
        self.db_path = db_path

    def get_db_path(self, config: dict) -> str:
        return str(self.db_path)


def get_required_history(history: DbPlayHistory, file_path: str) -> PlayHistory:
    result = history.get_history(file_path)
    assert result is not None
    return result


def test_play_history_updates_indexed_video(tmp_path):
    media_root = tmp_path / "movies"
    media_root.mkdir()
    video_path = media_root / "Film" / "film.mkv"
    video_path.parent.mkdir()
    video_path.touch()
    db_path = tmp_path / "movies.db"
    DbMigrations(str(db_path)).run_migrations()
    with duckdb.connect(str(db_path)) as con:
        con.execute(
            "INSERT INTO media_file (file_path) VALUES (?)",
            (video_path.as_posix(),),
        )

    history = DbPlayHistory(MockSettingsState(media_root, db_path))

    assert get_required_history(history, str(video_path)).qty_played == 0
    assert history.record_playback(str(video_path))
    assert get_required_history(history, str(video_path)).qty_played == 1
    assert (
        get_required_history(history, str(video_path)).last_played
        == datetime.now().astimezone().date()
    )

    overridden_date = date(2020, 5, 17)
    assert history.set_qty_played(str(video_path), 7)
    assert history.set_last_played(str(video_path), overridden_date)
    assert get_required_history(history, str(video_path)).qty_played == 7
    assert get_required_history(history, str(video_path)).last_played == overridden_date


def test_play_history_does_not_report_unindexed_video_as_updated(tmp_path):
    media_root = tmp_path / "movies"
    media_root.mkdir()
    video_path = media_root / "missing.mkv"
    db_path = tmp_path / "movies.db"
    DbMigrations(str(db_path)).run_migrations()
    history = DbPlayHistory(MockSettingsState(media_root, db_path))

    assert history.get_history(str(video_path)) is None
    assert not history.record_playback(str(video_path))


def test_media_file_metadata_maps_to_filter_metadata():
    metadata = MediaFileMetadata(
        title="Film",
        year=2024,
        plot="A plot",
        score=None,
        rated="PG-13",
        runtime=7200,
        tags=["tag"],
        genres=["Drama"],
        actors=["Actor"],
        directors=["Director"],
    )

    assert metadata.to_movie_info() == {
        "title": "Film",
        "year": 2024,
        "plot": "A plot",
        "score": None,
        "rated": "PG-13",
        "runtime": 7200,
        "tags": ["tag"],
        "genres": ["Drama"],
        "actors": ["Actor"],
        "director": "Director",
    }
