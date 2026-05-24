import os
from pathlib import Path

from src.utils.log_util import LogUtil


class VideoFinder:
    """Utility class to locate video files within the file system."""

    VIDEO_EXTS = frozenset({".mkv", ".mp4", ".avi", ".ts", ".mpg", ".mpeg"})

    def __init__(self, log_util:LogUtil) -> None:
        self.log_util = log_util

    def find_associated_video(self, folder_path: str | None) -> str | None:
        """
        Searches for a video file.

        Priority logic:
        1. If image_path is provided, looks in the image's directory for a video with the same name.
        2. If no exact name match is found, returns the first video found in the directory.
        """

        if not folder_path or not os.path.isdir(folder_path):
            self.log_util.warn(f"{folder_path} not a dir")
            return None

        try:
            # largest fle prob video
            # directory_items = sorted(os.listdir(folder_path), reverse=True, key=os.path.getsize)

            # video name prob same as folder name
            # path_obj = Path(folder_path)
            # pattern = path_obj.stem + "*"
            # directory_items = sorted(path_obj.glob(pattern))

            # grab all
            directory_items = sorted(os.listdir(folder_path))
        except OSError as e:
            self.log_util.error(f"Error listdir {folder_path} {e}")
            return None

        folder_path_obj = Path(folder_path)
        for item in directory_items:
            # full_item_path = os.path.join(folder_path, item)
            full_item_path = folder_path_obj.joinpath(item)
            # print(f"find_associated_video: full_item_path{full_item_path} {full_item_path.suffix.lower()}")
            # if not os.path.isfile(full_item_path):
            if not full_item_path.is_file():
                continue

            # path_obj = Path(full_item_path)
            if full_item_path.suffix.lower() not in self.VIDEO_EXTS:
                continue

            # Return immediately if we find a name match
            return full_item_path.as_posix()

        return None
