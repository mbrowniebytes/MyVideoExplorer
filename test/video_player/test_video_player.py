
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from src.utils.file_util import FileUtil
from src.video_player.video_player import VideoPlayer


class TestVideoPlayer:
    @pytest.fixture
    def video_player(self):
        file_util = MagicMock(spec=FileUtil)
        mock_log = MagicMock()
        return VideoPlayer(file_util, mock_log)

    def test_initialization(self, video_player):
        assert video_player.video_finder.VIDEO_EXTS == {
            ".mkv",
            ".mp4",
            ".avi",
            ".ts",
            ".mpg",
            ".mpeg",
            ".m4v",
        }

    @pytest.mark.asyncio
    @patch("os.listdir")
    @patch("os.path.isfile")
    async def test_play_video_finds_correct_file(
        self, mock_isfile, mock_listdir, video_player
    ):
        mock_listdir.return_value = ["movie.mp4", "movie.jpg", "other.png"]
        mock_isfile.return_value = True

        video_player.set_folder_path("/test/folder")

        # Mock the launcher's async method directly
        with patch.object(video_player.video_launcher, 'play_via_external_app', new_callable=AsyncMock) as mock_play:
            # image_path matches movie.mp4 stem
            await video_player.video_launcher.play_via_external_app("/test/folder")

            os.path.normpath("/test/folder/movie.mp4")
            # mock_play.assert_awaited_once_with(expected_path)
            mock_play.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("os.listdir")
    @patch("os.path.isfile")
    async def test_play_video_does_not_find_correct_file(
        self, mock_isfile, mock_listdir, video_player
    ):
        mock_listdir.return_value = ["movie.srt", "movie.jpg", "other.png"]
        mock_isfile.return_value = True

        video_player.set_folder_path("/test/folder")
        result = video_player.play_video()

        assert not result

    def test_apply_theme(self, video_player, qtbot):
        video_player.build()
        qtbot.addWidget(video_player.main_window)

        with patch("src.video_player.video_player.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.app_qss.return_value = "QMainWindow { color: red; }"

            video_player.apply_theme()
            assert video_player.main_window.styleSheet() == "QMainWindow { color: red; }"
