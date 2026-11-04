import asyncio
from typing import Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMainWindow

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.video_player.video_finder import VideoFinder
from MyVideoExplorer.video_player.video_launcher import VideoLauncher


class VideoPlayer(QObject):
    """
    Controller for video playback UI and orchestration.
    """

    video_played = Signal(str)

    def __init__(self, file_util: FileUtil, log_util: LogUtil) -> None:
        super().__init__()
        self.log_util = log_util
        self.file_util = file_util
        self.video_finder = VideoFinder(log_util)
        self.video_launcher = VideoLauncher(log_util)
        self.active_folder_path: str | None = None
        self.main_window: QMainWindow | None = None
        self.internal_playback_engine: Any | None = None
        self.log_util.debug(f"Initializing {self.__class__.__name__}")

    def build(self) -> QMainWindow:
        """Constructs the main video player window."""
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("Video Player")
        self.main_window.resize(1200, 800)
        return self.main_window

    def set_folder_path(self, folder_path: str) -> None:
        """Sets the directory context for video discovery."""
        self.active_folder_path = folder_path

    def play_video(self, folder_path: str | None = None) -> bool:
        """
        Locates and plays a video.
        If source_image_path is provided, it tries to find a matching video name.
        """

        search_path = folder_path or self.active_folder_path
        target_video_path = self.video_finder.find_associated_video(search_path)

        if not target_video_path:
            self.log_util.warning("No video file found to play.")
            return False

        self.log_util.info(f"Launching video playback for: {target_video_path}")

        asyncio.create_task(
            self.video_launcher.play_via_external_app(target_video_path)
        )
        self.video_played.emit(target_video_path)

        return True

    def play_folder_with_external_app(self, folder_path: str | None) -> bool:
        """Open all videos in a folder as one OS-default playlist."""
        video_paths = self.video_finder.find_videos_in_folder(folder_path)
        if not video_paths:
            self.log_util.warning(f"No video files found in folder: {folder_path}")
            return False

        asyncio.create_task(
            self.video_launcher.play_videos_via_external_app(video_paths)
        )
        self.video_played.emit(video_paths[0])
        return True

    def play_video_with_player(
        self, executable: str, source_path: str, arguments: str = ""
    ) -> bool:
        """Find the selected media's video and launch it with a configured player."""
        target_video_path = self.video_finder.find_associated_video(source_path)
        if not target_video_path:
            self.log_util.warning("No video file found to play.")
            return False

        self.log_util.info(
            f"Launching video playback with {executable}: {target_video_path}"
        )
        asyncio.create_task(
            self.video_launcher.play_via_player(
                executable, target_video_path, arguments
            )
        )
        self.video_played.emit(target_video_path)
        return True

    def play_folder_with_player(
        self, executable: str, folder_path: str, arguments: str = ""
    ) -> bool:
        """Launch every video directly in a folder with a configured player."""
        video_paths = self.video_finder.find_videos_in_folder(folder_path)
        if not video_paths:
            self.log_util.warning(f"No video files found in folder: {folder_path}")
            return False

        self.log_util.info(
            f"Launching {len(video_paths)} video(s) with {executable} from "
            f"{folder_path}"
        )
        asyncio.create_task(
            self.video_launcher.play_videos_via_player(
                executable, video_paths, arguments
            )
        )
        self.video_played.emit(video_paths[0])
        return True

    def enqueue_folder_playlist(
        self,
        folder_path: str | None,
        executable: str | None = None,
        arguments: str = "",
    ) -> bool:
        """Enqueue all videos in a folder to a player.

        For VLC, uses a temp M3U8 playlist to avoid CLI argument length limits.
        For other players, passes files as CLI arguments.
        Falls back to OS default player if no executable is provided.
        """
        video_paths = self.video_finder.find_videos_in_folder(folder_path)
        if not video_paths:
            self.log_util.warning(f"No video files found in folder: {folder_path}")
            return False

        if executable:
            asyncio.create_task(
                self.video_launcher.enqueue_via_player(
                    executable, video_paths, arguments
                )
            )
        else:
            asyncio.create_task(
                self.video_launcher.play_videos_via_external_app(video_paths)
            )
        self.video_played.emit(video_paths[0])
        return True

    def enqueue_playlist_from_folders(
        self,
        folder_paths: list[str],
        executable: str | None = None,
        arguments: str = "",
    ) -> bool:
        """Enqueue all videos from the given folder list.

        Collects videos from each folder and its subfolders. Videos are
        deduplicated so overlapping folder hierarchies do not produce duplicates.
        """
        self.log_util.info(f"Enqueue playlist from {len(folder_paths)} folders")
        seen: set[str] = set()
        video_paths: list[str] = []
        for folder_path in folder_paths:
            videos = self.video_finder.find_videos_in_folder_recursive(folder_path)
            if videos:
                for v in videos:
                    if v not in seen:
                        seen.add(v)
                        video_paths.append(v)
                self.log_util.debug(f"Found {len(videos)} videos in {folder_path}")

        self.log_util.info(f"Collected {len(video_paths)} total videos")
        return self.enqueue_video_paths(video_paths, executable, arguments)

    def enqueue_video_paths(
        self,
        video_paths: list[str],
        executable: str | None = None,
        arguments: str = "",
    ) -> bool:
        """Enqueue the supplied video paths without discovering files on disk."""
        deduplicated_paths = list(dict.fromkeys(video_paths))
        if not deduplicated_paths:
            self.log_util.warning("No filtered video files to enqueue.")
            return False

        if executable:
            asyncio.create_task(
                self.video_launcher.enqueue_via_player(
                    executable, deduplicated_paths, arguments
                )
            )
        else:
            asyncio.create_task(
                self.video_launcher.play_videos_via_external_app(deduplicated_paths)
            )
        self.video_played.emit(deduplicated_paths[0])
        return True

    def stop_video(self) -> None:
        """Stops the current internal playback session."""
        if self.internal_playback_engine:
            self.internal_playback_engine.stop()

    def apply_theme(self) -> None:
        """Applies consistent styling to the player window."""
        if self.main_window is None:
            return

        theme_font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.main_window.setFont(theme_font)
        self.main_window.setStyleSheet(APP_THEME.app_qss())
