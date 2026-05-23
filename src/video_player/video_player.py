import os
import pathlib
import sys
from asyncio import subprocess

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
)

from src.theme.theme import APP_THEME
from src.utils.file_util import FileUtil


class VideoPlayer:
    VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".ts", ".mpg", ".mpeg"}

    def __init__(self, file_util: FileUtil, log_util) -> None:
        self.log_util = log_util
        self.player = None
        self.file_util = file_util
        self.folder_path = None
        self.window = None
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def build(self):
        self.window = QMainWindow()
        self.window.setWindowTitle("Video Player")
        self.window.resize(1200, 800)
        return self.window

    def set_folder_path(self, folder_path: str) -> None:
        self.folder_path = folder_path

    def play_video(self, image_path: str | None = None):
        """Play video from the current folder, or prefer the folder of image_path."""

        video_file = None

        folder_path = self.folder_path
        image_stem = None

        if image_path:
            image_path_obj = pathlib.Path(image_path)
            folder_path = str(image_path_obj.parent)
            image_stem = image_path_obj.stem.lower()

        if folder_path is None:
            return

        try:
            sorted_items = sorted(os.listdir(folder_path))
        except OSError:
            return

        # Prefer a video with the same base name as the clicked image.
        for item in sorted_items:
            full_path = os.path.join(folder_path, item)
            path_obj = pathlib.Path(full_path)
            ext = path_obj.suffix.lower()

            if not os.path.isfile(full_path) or ext not in self.VIDEO_EXTS:
                continue

            if image_stem and path_obj.stem.lower() == image_stem:
                video_file = full_path
                break

            if video_file is None:
                video_file = full_path

        if video_file is None:
            return

        self.play_using_external_vlc(video_file)

    def play_using_external_vlc(self, video_file):
        ext = pathlib.Path(video_file).suffix
        print(f"Playing video: {ext} {video_file}")

        # Use VLC's external player? Or system default.
        # For simplicity, use subprocess to open the file with the default associated application.
        try:
            # On Windows, use 'start' command via shell
            if os.name == "nt":
                os.startfile(video_file)
            else:
                # On macOS and Linux, use 'open' or 'xdg-open'
                subprocess.Popen(
                    ["open" if sys.platform == "darwin" else "xdg-open", video_file]
                )
        except Exception as e:
            print(f"Failed to launch external player: {e}")

    def play_using_internal_vlc(self, video_file):
        ext = pathlib.Path(video_file).suffix
        print(f"Playing video: {ext} {video_file}")

        # Create a new player instance for each video
        self.player = self.vlc_instance.media_player_new()

        # Set the media to play
        media = self.vlc_instance.media_new(video_file)
        self.player.set_media(media)

        self.window.show()

        self.player.set_hwnd(int(self.window.winId()))

        # Start playing
        self.player.play()

    def stop_video(self):
        """Stop the currently playing video"""
        if self.player:
            self.player.stop()

    def apply_theme(self) -> None:
        if self.window is None:
            return

        self.window.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.window.setStyleSheet(APP_THEME.app_qss())
