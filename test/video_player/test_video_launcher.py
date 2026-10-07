from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.video_player.video_launcher import VideoLauncher


@pytest.mark.asyncio
@patch("MyVideoExplorer.video_player.video_launcher.os.name", "nt")
@patch("MyVideoExplorer.video_player.video_launcher.subprocess.Popen")
async def test_windows_launches_file_through_explorer(mock_popen):
    launcher = VideoLauncher(MagicMock())

    await launcher.play_via_external_app(r"C:\Videos\My Movie.mp4")

    mock_popen.assert_called_once_with(["explorer.exe", r"C:\Videos\My Movie.mp4"])
