import os
import duckdb
from MyVideoExplorer.db.db_scan import DbScanUtil

def test_year_validation(tmp_path):
    db_path = str(tmp_path / "test.db")
    db_util = DbScanUtil(db_path)
    folder_path = str(tmp_path / "test_folder").replace(os.path.sep, '/')

    file1 = os.path.join(folder_path, "video1.mp4").replace(os.path.sep, '/')

    # Test empty year
    media_list = [
        {'path': file1, 'dir': folder_path, 'metadata': {'title': 'Movie 1', 'year': ''}}
    ]

    db_util.save_media(media_list, folder_path)

    # Verify it's NULL (None) in the DB
    con = duckdb.connect(db_path)
    data = con.execute("SELECT year FROM media_file").fetchone()
    assert data is not None
    assert data[0] is None
    con.close()
