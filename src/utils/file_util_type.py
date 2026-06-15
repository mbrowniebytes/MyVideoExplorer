
from pathlib import Path


class FileUtilType:
    """Strategy class for file type classification based on extensions and naming conventions."""

    VIDEO_EXTS = frozenset({".mkv", ".mp4", ".avi", ".ts", ".mpg", ".mpeg", ".m4v"})
    IMAGE_EXTS = frozenset({".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"})
    NFO_EXTS = frozenset({".nfo", ".xml"})

    def classify(self, name: str) -> str | None:
        """Determine the logical type of a file based on extension and naming conventions."""
        ext = Path(name).suffix.casefold()
        if ext in self.NFO_EXTS:
            return "nfo"
        if name.casefold().endswith("poster"):
            return "poster"
        if ext in self.VIDEO_EXTS:
            return "video"
        if ext in self.IMAGE_EXTS:
            return "image"
        return ext.lstrip(".") or None

    def is_video_file(self, path: str) -> bool:
        return Path(path).suffix.casefold() in self.VIDEO_EXTS

    def is_image_file(self, path: str) -> bool:
        return Path(path).suffix.casefold() in self.IMAGE_EXTS

    def is_nfo_file(self, path: str) -> bool:
        return Path(path).suffix.casefold() in self.NFO_EXTS
