from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.file_util_model import FileUtilModel


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

    def test_build_file_item_normalizes_to_posix(self, file_util, tmp_path):
        target = tmp_path / "movie.mp4"
        target.write_bytes(b"x")

        item = file_util.build_file_item(str(target))

        assert item.full_path == target.as_posix()
        assert "/" in item.full_path
        assert "\\" not in item.full_path

        poster = tmp_path / "folder-poster.png"
        poster.write_bytes(b"x")
        image = tmp_path / "image1.jpg"
        image.write_bytes(b"x")

        images, selected = file_util.get_images_from_folder(str(tmp_path))

        assert any(Path(img).as_posix() == image.as_posix() for img in images)
        assert selected in {image.as_posix(), poster.as_posix()}

    @patch("MyVideoExplorer.utils.file_util.FileUtil._scan_directory")
    def test_get_images_from_folder(self, _scan_directory, file_util):
        _scan_directory.return_value = [
            MockDirEntry(
                type="file", name="image1.jpg", full_path="/test/image1.jpg", depth=0
            ),
            MockDirEntry(
                type="file",
                name="folder-poster.png",
                full_path="/test/folder-poster.png",
                depth=0,
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

    @patch("MyVideoExplorer.utils.file_util.FileUtil._scan_directory")
    def test_get_images_from_folder_order(self, _scan_directory, file_util):
        _scan_directory.return_value = [
            MockDirEntry(
                type="file", name="other.jpg", full_path="/test/other.jpg", depth=0
            ),
            MockDirEntry(
                type="file",
                name="folder-poster.jpg",
                full_path="/test/poster.jpg",
                depth=0,
            ),
            MockDirEntry(
                type="file", name="fanart.jpg", full_path="/test/fanart.jpg", depth=0
            ),
        ]

        images, poster = file_util.get_images_from_folder(".")
        assert len(images) == 3
        assert "poster.jpg" in images[0]
        assert "fanart.jpg" in images[1]
        assert "other.jpg" in images[2]

    @patch("MyVideoExplorer.utils.file_util.FileUtil._scan_directory")
    def test_get_images_from_folder_poster_priority(self, _scan_directory, file_util):
        _scan_directory.return_value = [
            MockDirEntry(
                type="file",
                name="movie-poster.jpg",
                full_path="/test/movie-poster.jpg",
                depth=0,
            ),
            MockDirEntry(
                type="file", name="poster.jpg", full_path="/test/poster.jpg", depth=0
            ),
        ]

        images, poster = file_util.get_images_from_folder(".")
        assert poster == "/test/poster.jpg"

    def test_build_hierarchy_from_paths(self, file_util):
        paths = ["/root/sub/file.mp4", "/root/sub/file2.mp4", "/root/sub2/file3.mp4"]
        root = "/root"
        items = file_util.build_hierarchy_from_paths(paths, root)

        # Check folders: /root/sub, /root/sub2
        # Check files: /root/sub/file.mp4, /root/sub/file2.mp4, /root/sub2/file3.mp4

        assert len(items) == 5
        folders = [item for item in items if item.is_dir]
        files = [item for item in items if item.is_file]

        assert len(folders) == 2
        assert len(files) == 3

        # Check sub
        sub = next(f for f in folders if f.name == "sub")
        assert sub.depth == 1

        # Check file
        f = next(f for f in files if f.name == "file.mp4")
        assert f.depth == 2
