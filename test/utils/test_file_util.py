import pytest
from unittest.mock import patch
from src.utils.file_util import FileUtil
from src.utils.file_util_model import FileUtilModel


class TestFileUtil:
    @pytest.fixture
    def file_util(self):
        return FileUtil()

    def test_classify_file(self, file_util):
        assert file_util.classify_file("test.mp4") == "video"
        assert file_util.classify_file("test.nfo") == "nfo"
        assert file_util.classify_file("test.jpg") == "image"
        assert file_util.classify_file("test.txt") == "txt"

    def test_is_video_file(self, file_util):
        assert file_util.is_video_file("test.mkv") is True
        assert file_util.is_video_file("test.txt") is False

    @patch("src.utils.file_util.FileUtil.get_child_files")
    @patch("os.path.isfile")
    def test_get_images_from_folder(self, mock_isfile, mock_get_child, file_util):
        mock_isfile.return_value = True

        mock_get_child.return_value = [
            FileUtilModel(
                type="file", name="image1.jpg", full_path="/test/image1.jpg", depth=0
            ),
            FileUtilModel(
                type="file", name="video.mp4", full_path="/test/video.mp4", depth=0
            ),
        ]

        images, first = file_util.get_images_from_folder("/test")
        assert len(images) == 1
        assert "image1.jpg" in images[0]
