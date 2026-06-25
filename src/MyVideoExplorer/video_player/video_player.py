import asyncio
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMainWindow

from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.video_player.video_finder import VideoFinder
from MyVideoExplorer.video_player.video_launcher import VideoLauncher


class VideoPlayer:
    """
    Controller for video playback UI and orchestration.
    """

    def __init__(self, file_util: FileUtil, log_util:LogUtil) -> None:
        self.log_util = log_util
        self.file_util = file_util
        self.video_finder = VideoFinder(log_util)
        self.video_launcher = VideoLauncher(log_util)
        self.active_folder_path = None
        self.main_window = None
        self.internal_playback_engine = None
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
        target_video_path = self.video_finder.find_associated_video(
            search_path
        )

        if not target_video_path:
            self.log_util.warn("No video file found to play.")
            return False

        self.log_util.info(f"Launching video playback for: {target_video_path}")

        asyncio.create_task(self.video_launcher.play_via_external_app(target_video_path))

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
