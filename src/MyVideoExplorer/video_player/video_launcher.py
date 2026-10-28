import asyncio
import os
import subprocess
import sys

from MyVideoExplorer.utils.file_util import FileUtils
from MyVideoExplorer.utils.log_util import LogUtil


class VideoLauncher:
    """Handles the execution of video playback via system processes."""

    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util

    async def play_via_external_app(self, video_path: str) -> None:
        """Opens the video using the operating system's default application."""

        # test async
        # await asyncio.sleep(5)

        normalized_path = FileUtils.normalize_path(video_path)

        try:
            if os.name == "nt":  # Windows
                # works with vlc, caused qt env error with mpc-qt
                # await asyncio.to_thread(os.startfile, normalized_path)

                # works with mpc-qt, vlc
                # await asyncio.to_thread(
                #     subprocess.Popen,
                #     ["explorer.exe", normalized_path],
                # )

                # maybe works with both
                clean_env = {
                    key: value
                    for key, value in os.environ.items()
                    if not key.upper().startswith(("QT_", "QML_"))
                }
                await asyncio.to_thread(
                    subprocess.Popen,
                    [
                        "rundll32.exe",
                        "url.dll,FileProtocolHandler",
                        normalized_path,
                    ],
                    env=clean_env,
                )
            elif sys.platform == "darwin":  # macOS
                await asyncio.create_subprocess_exec("open", normalized_path)
            else:  # Linux / Unix
                await asyncio.create_subprocess_exec("xdg-open", normalized_path)
        except Exception as e:
            self.log_util.error(f"Failed to launch external player: {e}")
