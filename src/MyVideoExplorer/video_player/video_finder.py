from pathlib import Path

from MyVideoExplorer.utils.log_util import LogUtil


class VideoFinder:
    """Utility class to locate video files within the file system."""

    VIDEO_EXTS = frozenset({".mkv", ".mp4", ".avi", ".ts", ".mpg", ".mpeg", ".m4v"})

    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util

    def find_associated_video(self, folder_path: str | None) -> str | None:
        """
        Searches for a video file.

        Priority logic:
        1. If image_path is provided, looks in the image's directory for a video with the same name.
        2. If no exact name match is found, returns the first video found in the directory.
        """

        folder_path_obj = Path(folder_path) if folder_path else None
        if folder_path_obj is None or not folder_path_obj.is_dir():
            self.log_util.warning(f"{folder_path} not a dir")
            return None

        try:
            # largest fle prob video
            # directory_items = sorted(folder_path_obj.iterdir(), key=lambda p: p.stat().st_size, reverse=True)

            # video name prob same as folder name
            # pattern = folder_path_obj.name + "*"
            # directory_items = sorted(folder_path_obj.glob(pattern))

            # grab all
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

            # path_obj = Path(full_item_path)
            if full_item_path.suffix.lower() not in self.VIDEO_EXTS:
                continue

            # Return immediately if we find a name match
            return full_item_path.as_posix()

        return None
