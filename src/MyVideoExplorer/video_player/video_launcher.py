import asyncio
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from MyVideoExplorer.utils.file_util import FileUtils
from MyVideoExplorer.utils.log_util import LogUtil

CAPTURE_PLAYER_OUTPUT = False


class VideoLauncher:
    """Handles the execution of video playback via system processes."""

    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util

    async def play_via_external_app(self, video_path: str) -> None:
        """Opens the video using the operating system's default application."""
        normalized_path = FileUtils.normalize_path(video_path)
        if os.name == "nt":
            command = ["rundll32.exe", "url.dll,FileProtocolHandler", normalized_path]
        elif sys.platform == "darwin":
            command = ["open", normalized_path]
        else:
            command = ["xdg-open", normalized_path]
        await self._launch_process(command)

    async def play_videos_via_external_app(self, video_paths: list[str]) -> None:
        """Open an ordered playlist with the operating system's default application."""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".m3u8",
                prefix="myvideoexplorer-",
                delete=False,
            ) as playlist:
                playlist.write("#EXTM3U\n")
                for video_path in video_paths:
                    playlist.write(f"{Path(video_path).resolve().as_uri()}\n")
                playlist_path = playlist.name
            await self.play_via_external_app(playlist_path)
        except (OSError, ValueError) as error:
            self.log_util.error(f"Failed to create or open video playlist: {error}")

    async def play_via_player(
        self, executable: str, video_path: str, arguments: str = ""
    ) -> None:
        """Launch a configured player directly with the selected video file."""
        await self.play_videos_via_player(executable, [video_path], arguments)

    async def play_videos_via_player(
        self, executable: str, video_paths: list[str], arguments: str = ""
    ) -> None:
        """Launch a configured player with an ordered list of media files."""
        try:
            player_arguments = shlex.split(arguments)
            launch_video_paths = [
                os.path.normpath(FileUtils.normalize_path(video_path))
                if os.name == "nt"
                else FileUtils.normalize_path(video_path)
                for video_path in video_paths
            ]
            command = [executable, *player_arguments, *launch_video_paths]
            await self._launch_process(
                command,
                clean_environment=True,
                capture_output=CAPTURE_PLAYER_OUTPUT,
            )
        except Exception as e:
            self.log_util.error(
                f"Failed to launch configured player '{executable}': {e}"
            )

    @staticmethod
    def _clean_environment() -> dict[str, str]:
        return {
            key: value
            for key, value in os.environ.items()
            if not key.upper().startswith(("QT_", "QML_"))
        }

    async def _launch_process(
        self,
        command: list[str],
        cwd: str | None = None,
        *,
        clean_environment: bool = True,
        capture_output: bool = False,
    ) -> None:
        """Launch a process with the same environment cleanup on every platform."""
        try:
            command_line = (
                subprocess.list2cmdline(command)
                if os.name == "nt"
                else shlex.join(command)
            )
            self.log_util.info(f"Executing video command: {command_line}")
            process_env = self._clean_environment() if clean_environment else None
            if os.name == "nt":
                output, return_code = await asyncio.to_thread(
                    self._launch_windows_process,
                    command,
                    process_env,
                    cwd,
                    capture_output,
                )
            else:
                if capture_output:
                    process = await asyncio.create_subprocess_exec(
                        *command,
                        env=process_env,
                        cwd=cwd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    output, _ = await process.communicate()
                    return_code = process.returncode
                else:
                    await asyncio.create_subprocess_exec(
                        *command, env=process_env, cwd=cwd
                    )

            if capture_output:
                if output:
                    output_text = (
                        output.decode(errors="replace")
                        if isinstance(output, bytes)
                        else output
                    )
                    self.log_util.info(f"Video player output: {output_text.strip()}")
                self.log_util.info(
                    f"Video player process exited with return code {return_code}"
                )
        except Exception as e:
            self.log_util.error(f"Failed to launch process '{command[0]}': {e}")

    @staticmethod
    def _launch_windows_process(
        command: list[str],
        process_env: dict[str, str] | None,
        cwd: str | None,
        capture_output: bool,
    ) -> tuple[bytes | None, int | None]:
        if capture_output:
            process = subprocess.Popen(
                command,
                env=process_env,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            output, _ = process.communicate()
            return output, process.returncode

        subprocess.Popen(command, env=process_env, cwd=cwd)
        return None, None
