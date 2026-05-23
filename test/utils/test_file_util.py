import pytest
from unittest.mock import patch, MagicMock
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel


class MockDirEntry(FileUtilModel):
    def is_file(self, follow_symlinks=False):
        return self.is_file

    @property
    def path(self):
        return self.full_path

    def is_dir(self, follow_symlinks=False):
        return self.is_dir


class TestFileUtil:
    @pytest.fixture
    def mock_log_util(self):
        return MagicMock()

    @pytest.fixture
    def file_util(self, mock_log_util):
        return FileUtil(log_util=mock_log_util)

    def test_determine_file_category(self, file_util):
        assert file_util.file_type.classify("test.mp4") == "video"
        assert file_util.file_type.classify("test.nfo") == "nfo"
        assert file_util.file_type.classify("test.jpg") == "image"
        assert file_util.file_type.classify("poster.png") == "image"
        assert file_util.file_type.classify("test.txt") == "txt"

    def test_is_video_file(self, file_util):
        assert file_util.is_video_file("test.mkv") is True
        assert file_util.is_video_file("test.txt") is False

    @patch("src.utils.file_util.FileUtil._scan_directory")
    def test_get_images_from_folder(self, _scan_directory, file_util):
        _scan_directory.return_value = [
            MockDirEntry(
                type="file", name="image1.jpg", full_path="/test/image1.jpg", depth=0
            ),
            MockDirEntry(
                type="file", name="folder-poster.png", full_path="/test/folder-poster.png", depth=0
            ),
            MockDirEntry(
                type="file", name="video.mp4", full_path="/test/video.mp4", depth=0
            ),
        ]

        images, poster = file_util.get_images_from_folder(".")
        assert len(images) == 2
        assert any("image1.jpg" in img for img in images)
        assert poster is not None
        assert "folder-poster.png" in poster
