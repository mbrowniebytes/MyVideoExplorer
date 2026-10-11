from pathlib import Path

from MyVideoExplorer.utils.log_util import LogUtil


class VideoFinder:
    """Utility class to locate video files within the file system."""

    VIDEO_EXTS = frozenset({".mkv", ".mp4", ".avi", ".ts", ".mpg", ".mpeg", ".m4v"})
    IMAGE_EXTS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"})

    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util

    def find_associated_video(self, folder_path: str | None) -> str | None:
        """
        Searches for a video file.

        Priority logic:
        1. If a video file is provided, returns it directly.
        2. If an image/nfo path is provided, looks in the file's directory for a video with the same stem or first video.
        3. If a folder path is provided, returns the first video found in the directory.
        """

        folder_path_obj = Path(folder_path) if folder_path else None
        if folder_path_obj is None:
            return None

        suffix = folder_path_obj.suffix.lower()
        if suffix in self.VIDEO_EXTS:
            return folder_path_obj.as_posix()

        if suffix in self.IMAGE_EXTS or suffix == ".nfo":
            parent = folder_path_obj.parent
            for ext in self.VIDEO_EXTS:
                matching = parent / f"{folder_path_obj.stem}{ext}"
                if matching.is_file():
                    return matching.as_posix()
            folder_path_obj = parent

        if not folder_path_obj.is_dir():
            self.log_util.warning(f"{folder_path} not a dir")
            return None

        try:
            directory_items = sorted(
                folder_path_obj.iterdir(), key=lambda item: item.name
            )
        except OSError as e:
            self.log_util.error(f"Error listdir {folder_path} {e}")
            return None

        for item in directory_items:
            full_item_path = item
            if not full_item_path.is_file():
                continue

            if full_item_path.suffix.lower() not in self.VIDEO_EXTS:
                continue

            return full_item_path.as_posix()

        return None
