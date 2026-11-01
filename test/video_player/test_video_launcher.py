from unittest.mock import MagicMock, patch

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
