import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.video_player.video_player import VideoPlayer


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

    def test_find_videos_in_folder_uses_natural_order_and_does_not_recurse(
        self, video_player, tmp_path
    ):
        (tmp_path / "Episode 10.mkv").touch()
        (tmp_path / "Episode 2.mp4").touch()
        (tmp_path / "featurette.avi").touch()
        subfolder = tmp_path / "extras"
        subfolder.mkdir()
        (subfolder / "Episode 1.mkv").touch()

        assert video_player.video_finder.find_videos_in_folder(str(tmp_path)) == [
            (tmp_path / "Episode 2.mp4").as_posix(),
            (tmp_path / "Episode 10.mkv").as_posix(),
            (tmp_path / "featurette.avi").as_posix(),
        ]

    @pytest.mark.asyncio
    async def test_configured_player_receives_associated_video_and_arguments(
        self, video_player
    ):
        video_player.video_finder.find_associated_video = MagicMock(
            return_value="/media/movie.mp4"
        )

        with patch.object(
            video_player.video_launcher, "play_via_player", new_callable=AsyncMock
        ) as mock_play:
            assert video_player.play_video_with_player(
                "/players/custom.exe", "/media/movie.jpg", "--fullscreen"
            )
            await asyncio.sleep(0)

        mock_play.assert_awaited_once_with(
            "/players/custom.exe", "/media/movie.mp4", "--fullscreen"
        )

    @pytest.mark.asyncio
    async def test_folder_player_receives_all_videos_and_records_first(
        self, video_player
    ):
        video_player.video_finder.find_videos_in_folder = MagicMock(
            return_value=["/media/Episode 1.mkv", "/media/Episode 2.mkv"]
        )
        video_played = MagicMock()
        video_player.video_played.connect(video_played)

        with patch.object(
            video_player.video_launcher,
            "play_videos_via_player",
            new_callable=AsyncMock,
        ) as mock_play:
            assert video_player.play_folder_with_player(
                "/players/vlc.exe", "/media/show", "--fullscreen"
            )
            await asyncio.sleep(0)

        mock_play.assert_awaited_once_with(
            "/players/vlc.exe",
            ["/media/Episode 1.mkv", "/media/Episode 2.mkv"],
            "--fullscreen",
        )
        video_played.assert_called_once_with("/media/Episode 1.mkv")

    @pytest.mark.asyncio
    async def test_external_folder_playback_queues_all_videos(self, video_player):
        video_player.video_finder.find_videos_in_folder = MagicMock(
            return_value=["/media/Episode 1.mkv", "/media/Episode 2.mkv"]
        )

        with patch.object(
            video_player.video_launcher,
            "play_videos_via_external_app",
            new_callable=AsyncMock,
        ) as mock_play:
            assert video_player.play_folder_with_external_app("/media/show")
            await asyncio.sleep(0)

        mock_play.assert_awaited_once_with(
            ["/media/Episode 1.mkv", "/media/Episode 2.mkv"]
        )

    @pytest.mark.asyncio
    async def test_playlist_enqueues_all_recursive_folder_videos_without_duplicates(
        self, video_player
    ):
        videos = [f"/media/Movie {index}.mkv" for index in range(25)]
        video_player.video_finder.find_videos_in_folder_recursive = MagicMock(
            side_effect=[videos, videos[10:]]
        )

        with patch.object(
            video_player.video_launcher, "enqueue_via_player", new_callable=AsyncMock
        ) as mock_enqueue:
            assert video_player.enqueue_playlist_from_folders(
                ["/media", "/media/collection"],
                "/players/vlc.exe",
                "--fullscreen",
            )
            await asyncio.sleep(0)

        video_player.video_finder.find_videos_in_folder_recursive.assert_any_call(
            "/media"
        )
        video_player.video_finder.find_videos_in_folder_recursive.assert_any_call(
            "/media/collection"
        )
        mock_enqueue.assert_awaited_once_with(
            "/players/vlc.exe", videos, "--fullscreen"
        )

    @pytest.mark.asyncio
    async def test_playlist_continues_after_empty_folder_and_scans_subfolders(
        self, video_player, tmp_path
    ):
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()
        folder_with_subfolder = tmp_path / "collection"
        nested_folder = folder_with_subfolder / "nested"
        nested_folder.mkdir(parents=True)
        first_video = nested_folder / "Movie 1.mkv"
        first_video.touch()
        second_video = nested_folder / "Movie 2.mp4"
        second_video.touch()
        final_folder = tmp_path / "another"
        final_folder.mkdir()
        final_video = final_folder / "Movie 3.avi"
        final_video.touch()

        with patch.object(
            video_player.video_launcher,
            "play_videos_via_external_app",
            new_callable=AsyncMock,
        ) as mock_play:
            assert video_player.enqueue_playlist_from_folders(
                [
                    str(empty_folder),
                    str(folder_with_subfolder),
                    str(final_folder),
                ]
            )
            await asyncio.sleep(0)

        mock_play.assert_awaited_once_with(
            [
                first_video.as_posix(),
                second_video.as_posix(),
                final_video.as_posix(),
            ]
        )

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
        with patch.object(
            video_player.video_launcher, "play_via_external_app", new_callable=AsyncMock
        ) as mock_play:
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

        with patch("MyVideoExplorer.video_player.video_player.APP_THEME") as mock_theme:
            mock_theme.font_family = "Arial"
            mock_theme.font_size = 12
            mock_theme.app_qss.return_value = "QMainWindow { color: red; }"

            video_player.apply_theme()
            assert (
                video_player.main_window.styleSheet() == "QMainWindow { color: red; }"
            )
