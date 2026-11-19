from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from MyVideoExplorer.video_player.video_launcher import VideoLauncher


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
async def test_windows_launches_file_through_system_association():
    launcher = VideoLauncher(MagicMock())

    with patch.object(
        launcher,
        "_launch_process",
        new_callable=AsyncMock,
    ) as mock_launch:
        with patch.dict(
            "MyVideoExplorer.video_player.video_launcher.os.environ",
            {"QT_PLUGIN_PATH": "app/qt/plugins", "KEEP_ME": "value"},
        ):
            await launcher.play_via_external_app(r"C:\Videos\My Movie.mp4")

    args, _kwargs = mock_launch.call_args
    command = args[0]
    assert command == [
        "rundll32.exe",
        "url.dll,FileProtocolHandler",
        "C:/Videos/My Movie.mp4",
    ]


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.os.path.normpath")
async def test_windows_launches_configured_player_with_video_path(
    mock_normpath,
):
    log_util = MagicMock()
    launcher = VideoLauncher(log_util)
    mock_normpath.side_effect = lambda p: p

    with (
        patch(
            "MyVideoExplorer.video_player.video_launcher.CAPTURE_PLAYER_OUTPUT",
            True,
        ),
        patch.object(
            launcher,
            "_launch_process",
            new_callable=AsyncMock,
        ) as mock_launch,
        patch.dict(
            "MyVideoExplorer.video_player.video_launcher.os.environ",
            {"QT_PLUGIN_PATH": "app/qt/plugins", "KEEP_ME": "value"},
        ),
    ):
        await launcher.play_via_player(
            r"C:\Apps\VLC\vlc.exe", r"C:\Videos\My Movie.mp4"
        )

    args, _kwargs = mock_launch.call_args
    command = args[0]
    assert command == ["C:\\Apps\\VLC\\vlc.exe", "C:/Videos/My Movie.mp4"]
    assert _kwargs.get("clean_environment") is True
    assert _kwargs.get("capture_output") is True


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
async def test_vlc_output_capture_is_disabled_by_default():
    log_util = MagicMock()
    launcher = VideoLauncher(log_util)

    with patch.object(
        launcher, "_launch_process", new_callable=AsyncMock
    ) as mock_launch:
        await launcher.play_via_player(
            r"C:\Apps\VLC\vlc.exe", r"C:\Videos\My Movie.mp4"
        )

    _args, _kwargs = mock_launch.call_args
    assert _kwargs.get("capture_output") is False
    assert _kwargs.get("clean_environment") is True


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.os.path.normpath")
async def test_custom_player_uses_windows_path_and_clean_environment(
    mock_normpath,
):
    launcher = VideoLauncher(MagicMock())
    mock_normpath.side_effect = lambda p: p

    with patch.object(
        launcher, "_launch_process", new_callable=AsyncMock
    ) as mock_launch:
        await launcher.play_via_player(
            r"C:\Apps\Custom\player.exe", r"C:\Videos\My Movie.mp4"
        )

    args, _kwargs = mock_launch.call_args
    command = args[0]
    assert command == ["C:\\Apps\\Custom\\player.exe", "C:/Videos/My Movie.mp4"]
    assert _kwargs.get("clean_environment") is True
    assert _kwargs.get("capture_output") is False


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.os.path.normpath")
async def test_custom_arguments_are_passed_before_video_path(mock_normpath):
    log_util = MagicMock()
    launcher = VideoLauncher(log_util)
    mock_normpath.side_effect = lambda p: p

    with patch.object(
        launcher, "_launch_process", new_callable=AsyncMock
    ) as mock_launch:
        await launcher.play_via_player(
            r"C:\Apps\Custom\player.exe",
            r"C:\Videos\My Movie.mp4",
            '--fullscreen --profile "My Profile"',
        )

    args, _kwargs = mock_launch.call_args
    command = args[0]
    assert command == [
        "C:\\Apps\\Custom\\player.exe",
        "--fullscreen",
        "--profile",
        "My Profile",
        "C:/Videos/My Movie.mp4",
    ]
    assert _kwargs.get("clean_environment") is True
    assert _kwargs.get("capture_output") is False


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.os.path.normpath")
async def test_configured_player_receives_all_playlist_paths(mock_normpath):
    launcher = VideoLauncher(MagicMock())
    mock_normpath.side_effect = lambda p: p

    with patch.object(
        launcher, "_launch_process", new_callable=AsyncMock
    ) as mock_launch:
        await launcher.play_videos_via_player(
            r"C:\Apps\VLC\vlc.exe",
            [r"C:\Videos\Episode 1.mkv", r"C:\Videos\Episode 2.mkv"],
            "--fullscreen",
        )

    args, _ = mock_launch.call_args
    command = args[0]
    assert command == [
        "C:\\Apps\\VLC\\vlc.exe",
        "--fullscreen",
        "C:/Videos/Episode 1.mkv",
        "C:/Videos/Episode 2.mkv",
    ]


@pytest.mark.asyncio
async def test_external_app_opens_all_videos_from_a_playlist():
    launcher = VideoLauncher(MagicMock())
    video_paths = ["/media/Episode 1.mkv", "/media/Episode 2.mkv"]

    with patch.object(
        launcher, "play_via_external_app", new_callable=AsyncMock
    ) as mock_open:
        await launcher.play_videos_via_external_app(video_paths)

    await_args = mock_open.await_args
    assert await_args is not None
    playlist_path = Path(await_args.args[0])
    try:
        assert playlist_path.is_absolute(), (
            "Playlist path should be absolute for OS default handler"
        )
        assert playlist_path.name == "myvideoexplorer-os-default.m3u8"
        assert playlist_path.read_text(encoding="utf-8").splitlines() == [
            "#EXTM3U",
            Path(video_paths[0]).resolve().as_uri(),
            Path(video_paths[1]).resolve().as_uri(),
        ]
    finally:
        playlist_path.unlink()


@pytest.mark.asyncio
async def test_single_video_via_external_app_passes_file_directly():
    """When there's only one video, pass it directly without creating a playlist."""
    launcher = VideoLauncher(MagicMock())
    video_path = "/media/Movie.mkv"

    with patch.object(
        launcher, "play_via_external_app", new_callable=AsyncMock
    ) as mock_open:
        await launcher.play_videos_via_external_app([video_path])

    await_args = mock_open.await_args
    assert await_args is not None
    assert await_args.args[0] == video_path


@pytest.mark.asyncio
async def test_enqueue_uses_temp_playlist_even_for_one_video():
    launcher = VideoLauncher(MagicMock())
    video_path = "/media/Movie.mkv"

    with patch.object(
        launcher, "_launch_process", new_callable=AsyncMock
    ) as mock_launch:
        await launcher.enqueue_via_player("/players/vlc", [video_path])

    await_args = mock_launch.await_args
    assert await_args is not None
    command = await_args.args[0]
    playlist_path = Path(command[-1])
    try:
        assert command[0] == "/players/vlc"
        assert playlist_path.parent == Path("tmp")
        assert playlist_path.name == "myvideoexplorer-vlc.m3u8"
        assert playlist_path.read_text(encoding="utf-8").splitlines() == [
            "#EXTM3U",
            Path(video_path).resolve().as_uri(),
        ]
    finally:
        playlist_path.unlink()
