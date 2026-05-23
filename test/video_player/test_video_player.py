import pytest
import os
from unittest.mock import MagicMock, patch
from src.utils.file_util import FileUtil
from src.video_player.video_player import VideoPlayer


class TestVideoPlayer:
    @pytest.fixture
    def video_player(self):
        file_util = MagicMock(spec=FileUtil)
        mock_log = MagicMock()
        return VideoPlayer(file_util, mock_log)

    def test_initialization(self, video_player):
        assert video_player.VIDEO_EXTS == {
            ".mkv",
            ".mp4",
            ".avi",
            ".ts",
            ".mpg",
            ".mpeg",
        }

    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.startfile")
    def test_play_video_finds_correct_file(
        self, mock_startfile, mock_isfile, mock_listdir, video_player
    ):
        mock_listdir.return_value = ["movie.mp4", "movie.jpg", "other.mkv"]
        mock_isfile.return_value = True

        video_player.set_folder_path("/test/folder")
        # image_path matches movie.mp4 stem
        video_player.play_video("/test/folder/movie.jpg")

        # Should call startfile with movie.mp4
        expected_path = os.path.normpath("/test/folder/movie.mp4")
        mock_startfile.assert_called_once()
        actual_path = os.path.normpath(mock_startfile.call_args[0][0])
        assert actual_path == expected_path

    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("os.startfile")
    def test_play_video_prefers_image_stem(
        self, mock_startfile, mock_isfile, mock_listdir, video_player
    ):
        mock_listdir.return_value = ["first.mp4", "second.mp4"]
        mock_isfile.return_value = True

        video_player.set_folder_path("/test/folder")
        # should pick second.mp4 because of stem match
        video_player.play_video("/test/folder/second.jpg")

        actual_path = os.path.normpath(mock_startfile.call_args[0][0])
        assert "second.mp4" in actual_path

    def test_apply_theme(self, video_player, qtbot):
        video_player.build()
        qtbot.addWidget(video_player.window)

        with patch("src.video_player.video_player.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.app_qss.return_value = "QMainWindow { color: red; }"

            video_player.apply_theme()
            assert video_player.window.styleSheet() == "QMainWindow { color: red; }"
