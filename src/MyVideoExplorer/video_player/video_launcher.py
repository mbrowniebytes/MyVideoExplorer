import os
import sys
import asyncio
from pathlib import Path

from MyVideoExplorer.utils.log_util import LogUtil


class VideoLauncher:
    """Handles the execution of video playback via system processes."""

    def __init__(self, log_util:LogUtil) -> None:
        self.log_util = log_util

    async def play_via_external_app(self, video_path: str) -> None:
        """Opens the video using the operating system's default application."""

        # test async
        # await asyncio.sleep(5)

        normalized_path = str(Path(video_path))

        try:
            if os.name == "nt":  # Windows
                await asyncio.to_thread(os.startfile, normalized_path)
            elif sys.platform == "darwin":  # macOS
                await asyncio.create_subprocess_exec("open", normalized_path)
            else:  # Linux / Unix
                await asyncio.create_subprocess_exec("xdg-open", normalized_path)
        except Exception as e:
            self.log_util.error(f"Failed to launch external player: {e}")
