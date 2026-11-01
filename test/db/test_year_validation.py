import datetime
from pathlib import Path

import duckdb

from MyVideoExplorer.db.db_scan import DbScanUtil
from MyVideoExplorer.utils.file_util import FileUtil


def get_year(db_path: str, file_path: str) -> int | None:
    with duckdb.connect(Path(db_path).as_posix()) as con:
        result = con.execute(
            "SELECT year FROM media_file WHERE file_path = ?",
            (Path(file_path).as_posix(),),
        ).fetchone()
    return result[0] if result else None


def test_year_validation(tmp_path):
    db_path = str(tmp_path / "test.db")
    db_util = DbScanUtil(db_path)
    folder_path = str(tmp_path / "test_folder")

    file1 = str(Path(folder_path) / "video1.mp4")

    # Test empty year without year in filename
    media_list = [
        {
            "file_path": file1,
            "metadata": {"title": "Movie 1", "year": ""},
        }
    ]

    db_util.save_media(media_list, folder_path)

    # Verify it's NULL (None) in the DB
    assert get_year(db_path, file1) is None


def test_year_fallback_from_filename(tmp_path):
    db_path = str(tmp_path / "test_fallback.db")
    db_util = DbScanUtil(db_path)
    folder_path = str(tmp_path / "movies")

    file_bracket = str(Path(folder_path) / "The Matrix (1999).mp4")
    file_dot = str(Path(folder_path) / "Inception.2010.1080p.mkv")

    media_list = [
        {"file_path": file_bracket, "metadata": {"title": "The Matrix", "year": 0}},
        {"file_path": file_dot, "metadata": {"title": "Inception", "year": ""}},
    ]

    db_util.save_media(media_list, folder_path)

    assert get_year(db_path, file_bracket) == 1999
    assert get_year(db_path, file_dot) == 2010


def test_year_fallback_from_folder(tmp_path):
    db_path = str(tmp_path / "test_folder_fallback.db")
    db_util = DbScanUtil(db_path)
    movie_folder = str(tmp_path / "movies" / "Interstellar (2014)")
    video_file = str(Path(movie_folder) / "movie.mkv")

    media_list = [
        {"file_path": video_file, "metadata": None},
    ]

    db_util.save_media(media_list, movie_folder)

    assert get_year(db_path, video_file) == 2014


def test_nfo_year_takes_precedence_over_filename_and_parent(tmp_path):
    db_path = str(tmp_path / "nfo_year.db")
    db_util = DbScanUtil(db_path)
    folder_path = tmp_path / "Film (2014)"
    file_path = folder_path / "Film (1999).mkv"

    db_util.save_media(
        [{"file_path": str(file_path), "metadata": {"year": "2001"}}],
        str(folder_path),
    )

    assert get_year(db_path, str(file_path)) == 2001


def test_year_fallback_range_and_filename_precedence(tmp_path):
    current_year = datetime.datetime.now(datetime.UTC).year
    accepted_future = current_year + 10
    rejected_future = current_year + 11

    assert FileUtil.extract_year_from_path("Movie.1900.mkv") == 1900
    assert (
        FileUtil.extract_year_from_path(f"Movie ({accepted_future}).mkv")
        == accepted_future
    )
    assert FileUtil.extract_year_from_path(f"Movie ({rejected_future}).mkv") is None
    assert FileUtil.extract_year_from_path("Movie (1899).mkv") is None
    assert FileUtil.extract_year_from_path("Movie.1080p.2160p.mkv") is None
    assert (
        FileUtil.extract_year_from_path(
            str(tmp_path / "Folder (2014)" / "Film (1999).mkv")
        )
        == 1999
    )


def test_scan_normalizes_windows_paths_to_posix(tmp_path):
    db_path = str(tmp_path / "posix_paths.db")
    db_util = DbScanUtil(db_path)
    windows_path = r"C:\Media\Film (2020)\movie.mkv"

    db_util.save_media(
        [{"file_path": windows_path, "metadata": {"year": 2020}}],
        r"C:\Media\Film (2020)",
    )

    with duckdb.connect(Path(db_path).as_posix()) as con:
        file_path, media_path = con.execute(
            "SELECT file_path, media_path FROM media_file"
        ).fetchone()
    assert file_path == "C:/Media/Film (2020)/movie.mkv"
    assert media_path == "C:/Media/Film (2020)"
