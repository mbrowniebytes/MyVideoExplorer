import pytest
import os
from unittest.mock import MagicMock, patch
from MyVideoExplorer.db.db_scan_worker import ScanWorker
from MyVideoExplorer.utils.file_util import FileUtil

class TestScanWorker:
    @pytest.fixture
    def mock_file_util(self):
        return MagicMock(spec=FileUtil)

    @pytest.fixture
    def mock_nfo_util(self):
        return MagicMock()

    @pytest.fixture
    def folder_config(self):
        return {"label": "Test", "path": "D:/TestVideos"}

    @patch("MyVideoExplorer.db.db_scan_worker.DbScanUtil")
    @patch("os.walk")
    @patch("os.path.isdir", return_value=True)
    def test_run(self, mock_isdir, mock_walk, mock_db_util_class, folder_config, mock_file_util, mock_nfo_util):
        # Mock file system
        mock_walk.return_value = [
            ("D:/TestVideos", ["subdir"], ["video1.mp4", "movie.nfo"]),
            ("D:/TestVideos/subdir", [], ["video2.mkv"]),
        ]

        # Setup mock file util for NFO finding
        mock_file_util.find_nfo_in_list.return_value = "D:/TestVideos/movie.nfo"

        # Setup mock NFO util
        mock_nfo_util.parse_nfo_file.return_value = {"title": "Test Movie"}

        # Instantiate worker
        worker = ScanWorker(folder_config, mock_file_util, mock_nfo_util)

        # Mock DB util instance
        mock_db_util = MagicMock()
        mock_db_util_class.return_value = mock_db_util

        # Run
        worker.run()

        # Assertions
        assert mock_db_util.save_media.called
        assert mock_db_util.save_stats.called

        saved_media = mock_db_util.save_media.call_args[0][0]
        assert len(saved_media) == 2
        assert saved_media[0]["path"] == "D:/TestVideos/video1.mp4"
        assert saved_media[0]["metadata"] == {"title": "Test Movie"}
        assert saved_media[1]["path"] == "D:/TestVideos/subdir/video2.mkv"
        assert saved_media[1]["metadata"] == {"title": "Test Movie"}

        saved_stats = mock_db_util.save_stats.call_args[0][0]
        assert saved_stats["videos_count"] == 2

    @patch("MyVideoExplorer.db.db_scan_worker.DbScanUtil")
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("os.walk")
    @patch("os.path.isdir", return_value=True)
    def test_run_replaces_db(self, mock_isdir, mock_walk, mock_remove, mock_exists, mock_db_util_class, folder_config, mock_file_util, mock_nfo_util):
        mock_exists.return_value = True

        worker = ScanWorker(folder_config, mock_file_util, mock_nfo_util)
        worker.run()

        assert mock_remove.called
        # Check if remove was called with the db path
        expected_path = os.path.join("db", "Test.db")
        assert mock_remove.call_args[0][0].endswith(expected_path) or mock_remove.call_args[0][0].endswith(expected_path.replace("\\", "/"))

    def test_backup_db(self, tmp_path, folder_config, mock_file_util, mock_nfo_util):
        db_dir = tmp_path / "db"
        db_dir.mkdir()
        db_file = db_dir / "Test.db"
        db_file.write_text("dummy db content")

        worker = ScanWorker(folder_config, mock_file_util, mock_nfo_util)

        # Call _backup_db
        worker._backup_db(str(db_file))

        # Assert backup created
        import datetime
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        backup_file = db_dir / f"Test_{today_str}.db"
        assert backup_file.exists()
        assert backup_file.read_text() == "dummy db content"

    def test_backup_db_rotation(self, tmp_path, folder_config, mock_file_util, mock_nfo_util):
        import time
        db_dir = tmp_path / "db"
        db_dir.mkdir()
        db_file = db_dir / "Test.db"
        db_file.write_text("dummy db content")

        worker = ScanWorker(folder_config, mock_file_util, mock_nfo_util)

        # Create 6 old backups manually
        for i in range(6):
            backup_file = db_dir / f"Test_2020-01-0{i+1}.db"
            backup_file.write_text("old")
            # Set mtime to be in the past
            # In Windows, setting mtime on files might be tricky,
            # but for this test, we can just use time.sleep
            time.sleep(0.1)

        # Call _backup_db
        worker._backup_db(str(db_file))

        # Assert total backups = 5 (the latest 5, including the one we just created for today)
        all_backups = list(db_dir.glob("Test_*.db"))
        assert len(all_backups) == 5

        # The oldest one (Test_2020-01-01.db) should be gone
        assert not (db_dir / "Test_2020-01-01.db").exists()
