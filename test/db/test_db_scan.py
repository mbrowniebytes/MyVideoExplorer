import datetime
from pathlib import Path

import duckdb
import pytest

from MyVideoExplorer.db.db_scan import DbScanUtil

class TestDbScanUtil:
    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test.db")

    @pytest.fixture
    def db_util(self, db_path):
        return DbScanUtil(db_path)

    def test_init_db(self, db_path):
        DbScanUtil(db_path)
        assert Path(db_path).exists()
        con = duckdb.connect(db_path)
        tables = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [table[0] for table in tables]
        assert "media_file" in table_names
        assert "media_path_stats" in table_names
        con.close()

    def test_save_and_get_stats(self, db_util, db_path):
        stats = {
            'media_path': '/test/path',
            'subfolders_count': 1,
            'files_count': 2,
            'images_count': 0,
            'videos_count': 1,
            'nfo_count': 0,
            'other_count': 0,
            'last_scanned': datetime.datetime.now(datetime.UTC)
        }
        db_util.save_stats(stats)
        retrieved = db_util.get_stats('/test/path')
        assert retrieved is not None
        assert retrieved[0] == '/test/path'
        assert retrieved[1] == 1
        assert retrieved[2] == 2

    def test_save_media(self, db_util, db_path):
        media_list = [
            {'file_path': '/test/path/video1.mp4', 'metadata': {'title': 'Movie 1'}},
            {'file_path': '/test/path/video2.mp4', 'metadata': {'title': 'Movie 2'}}
        ]
        db_util.save_media(media_list, '/test/path')
        con = duckdb.connect(db_path)
        data = con.execute("SELECT file_path, title FROM media_file").fetchall()
        assert len(data) == 2
        assert data[0][0] == '/test/path/video1.mp4'
        assert data[0][1] == 'Movie 1'
        con.close()
