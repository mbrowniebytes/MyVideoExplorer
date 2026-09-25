from pathlib import Path

import duckdb

from MyVideoExplorer.db.db_scan import DbScanUtil


def test_runtime_conversion_issue(tmp_path):
    db_path = str(tmp_path / "test.db")
    db_util = DbScanUtil(db_path)
    folder_path = str(tmp_path / "test_folder")

    file1 = str(Path(folder_path) / "video1.mp4")

    media_list = [
        {
            "path": file1,
            "dir": folder_path,
            "metadata": {"title": "Movie 1", "runtime": ""},
        }
    ]

    # This should now succeed
    db_util.save_media(media_list, folder_path)

    # Verify it's in the DB
    con = duckdb.connect(db_path)
    data = con.execute("SELECT runtime FROM media_file").fetchone()
    assert data is not None
    assert data[0] == 0
    con.close()


def test_runtime_conversion_seconds(tmp_path):
    db_path = str(tmp_path / "test.db")
    db_util = DbScanUtil(db_path)
    folder_path = str(tmp_path / "test_folder")

    file1 = str(Path(folder_path) / "video1.mp4")

    media_list = [
        {
            "path": file1,
            "dir": folder_path,
            "metadata": {"title": "Movie 1", "runtime": "10"},
        }
    ]

    # This should now succeed
    db_util.save_media(media_list, folder_path)

    # Verify it's in the DB (10 minutes * 60 = 600 seconds)
    con = duckdb.connect(db_path)
    data = con.execute("SELECT runtime FROM media_file").fetchone()
    assert data is not None
    assert data[0] == 600
    con.close()
