import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from MyVideoExplorer.video_player.video_launcher import VideoLauncher


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_windows_launches_file_through_system_association(mock_popen):
    launcher = VideoLauncher(MagicMock())

    with patch.dict(
        "MyVideoExplorer.video_player.video_launcher.os.environ",
        {"QT_PLUGIN_PATH": "app/qt/plugins", "KEEP_ME": "value"},
    ):
        await launcher.play_via_external_app(r"C:\Videos\My Movie.mp4")

    args, kwargs = mock_popen.call_args
    assert args == (
        [
            "rundll32.exe",
            "url.dll,FileProtocolHandler",
            "C:/Videos/My Movie.mp4",
        ],
    )
    assert "QT_PLUGIN_PATH" not in kwargs["env"]
    assert kwargs["env"]["KEEP_ME"] == "value"


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_windows_launches_configured_player_with_video_path(mock_popen):
    log_util = MagicMock()
    launcher = VideoLauncher(log_util)
    process = MagicMock()
    process.communicate.return_value = (b"VLC started", None)
    process.returncode = 0
    mock_popen.return_value = process

    with (
        patch(
            "MyVideoExplorer.video_player.video_launcher.CAPTURE_PLAYER_OUTPUT",
            True,
        ),
        patch.dict(
            "MyVideoExplorer.video_player.video_launcher.os.environ",
            {"QT_PLUGIN_PATH": "app/qt/plugins", "KEEP_ME": "value"},
        ),
    ):
        await launcher.play_via_player(
            r"C:\Apps\VLC\vlc.exe", r"C:\Videos\My Movie.mp4"
        )

    args, kwargs = mock_popen.call_args
    assert args == (["C:\\Apps\\VLC\\vlc.exe", "C:\\Videos\\My Movie.mp4"],)
    assert "QT_PLUGIN_PATH" not in kwargs["env"]
    assert kwargs["cwd"] is None
    assert kwargs["stdout"] == subprocess.PIPE
    assert kwargs["stderr"] == subprocess.STDOUT
    log_util.info.assert_any_call(
        'Executing video command: C:\\Apps\\VLC\\vlc.exe "C:\\Videos\\My Movie.mp4"'
    )
    log_util.info.assert_any_call("Video player output: VLC started")
    log_util.info.assert_any_call("Video player process exited with return code 0")


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_vlc_output_capture_is_disabled_by_default(mock_popen):
    log_util = MagicMock()
    launcher = VideoLauncher(log_util)

    await launcher.play_via_player(r"C:\Apps\VLC\vlc.exe", r"C:\Videos\My Movie.mp4")

    _, kwargs = mock_popen.call_args
    assert "QT_PLUGIN_PATH" not in kwargs["env"]
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs
    log_util.info.assert_called_once()


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_custom_player_uses_windows_path_and_clean_environment(mock_popen):
    launcher = VideoLauncher(MagicMock())

    await launcher.play_via_player(
        r"C:\Apps\Custom\player.exe", r"C:\Videos\My Movie.mp4"
    )

    args, kwargs = mock_popen.call_args
    assert args == (["C:\\Apps\\Custom\\player.exe", "C:\\Videos\\My Movie.mp4"],)
    assert kwargs["env"] == launcher._clean_environment()
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_custom_arguments_are_passed_before_video_path(mock_popen):
    log_util = MagicMock()
    launcher = VideoLauncher(log_util)

    await launcher.play_via_player(
        r"C:\Apps\Custom\player.exe",
        r"C:\Videos\My Movie.mp4",
        '--fullscreen --profile "My Profile"',
    )

    args, kwargs = mock_popen.call_args
    assert args == (
        [
            "C:\\Apps\\Custom\\player.exe",
            "--fullscreen",
            "--profile",
            "My Profile",
            "C:\\Videos\\My Movie.mp4",
        ],
    )
    assert kwargs["cwd"] is None
    assert "QT_PLUGIN_PATH" not in kwargs["env"]
    assert "stdout" not in kwargs
    assert "stderr" not in kwargs
    log_util.info.assert_called_once_with(
        "Executing video command: C:\\Apps\\Custom\\player.exe --fullscreen "
        '--profile "My Profile" "C:\\Videos\\My Movie.mp4"'
    )


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_configured_player_receives_all_playlist_paths(mock_popen):
    launcher = VideoLauncher(MagicMock())

    await launcher.play_videos_via_player(
        r"C:\Apps\VLC\vlc.exe",
        [r"C:\Videos\Episode 1.mkv", r"C:\Videos\Episode 2.mkv"],
        "--fullscreen",
    )

    args, _ = mock_popen.call_args
    assert args == (
        [
            "C:\\Apps\\VLC\\vlc.exe",
            "--fullscreen",
            "C:\\Videos\\Episode 1.mkv",
            "C:\\Videos\\Episode 2.mkv",
        ],
    )


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
        assert playlist_path.suffix == ".m3u8"
        assert playlist_path.read_text(encoding="utf-8").splitlines() == [
            "#EXTM3U",
            Path(video_paths[0]).resolve().as_uri(),
            Path(video_paths[1]).resolve().as_uri(),
        ]
    finally:
        playlist_path.unlink()
