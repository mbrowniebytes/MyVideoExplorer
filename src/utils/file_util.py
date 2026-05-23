from __future__ import annotations

import os
from pathlib import Path

from src.utils.file_util_model import FileUtilModel


class FileUtil:
    VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".ts", ".mpg", ".mpeg"}
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
    NFO_EXTS = {".nfo", ".xml"}

    def __init__(self, log_util=None):
        super().__init__()
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _normalize_path(self, path: str) -> str:
        if not path:
            return ""
        return os.path.normpath(path)

    def _safe_scandir(self, path: str):
        try:
            with os.scandir(path) as entries:
                return sorted(entries, key=lambda entry: entry.name)
        except (OSError, PermissionError):
            return None

    def list_directory(self, path: str) -> list[FileUtilModel]:
        """
        Return direct children for a folder, sorted by name.
        """
        items: list[FileUtilModel] = []

        path = self._normalize_path(path)
        if not path or not os.path.isdir(path):
            return items

        sorted_entries = self._safe_scandir(path)
        if sorted_entries is None:
            return items

        for entry in sorted_entries:
            try:
                full_path = self._normalize_path(entry.path)
                name = entry.name

                if entry.is_dir(follow_symlinks=False):
                    items.append(
                        FileUtilModel(
                            type="dir",
                            name=name,
                            full_path=full_path,
                            depth=0,
                        )
                    )
                    continue

                if not entry.is_file(follow_symlinks=False):
                    continue

                items.append(self.build_file_item(full_path))
            except (OSError, PermissionError):
                continue

        return items

    def get_child_dirs(self, path: str) -> list[FileUtilModel]:
        return [item for item in self.list_directory(path) if item.is_dir]

    def get_child_files(self, path: str) -> list[FileUtilModel]:
        return [item for item in self.list_directory(path) if item.is_file]

    def get_files_from_path(self, path: str, depth: int = 0) -> list[FileUtilModel]:
        """
        Recursively collect directory and file metadata for a path.
        """
        items: list[FileUtilModel] = []

        path = self._normalize_path(path)
        if not path or not os.path.isdir(path):
            return items

        sorted_entries = self._safe_scandir(path)
        if sorted_entries is None:
            return items

        for entry in sorted_entries:
            try:
                full_path = self._normalize_path(entry.path)
                name = entry.name

                if entry.is_dir(follow_symlinks=False):
                    items.append(
                        FileUtilModel(
                            type="dir",
                            name=name,
                            full_path=full_path,
                            depth=depth,
                        )
                    )
                    items.extend(self.get_files_from_path(full_path, depth + 1))
                    continue

                if not entry.is_file(follow_symlinks=False):
                    continue

                items.append(self.build_file_item(full_path, depth=depth))
            except (OSError, PermissionError):
                continue

        return items

    def get_images_from_folder(self, folder_path: str) -> tuple[list[str], str | None]:
        items = self.get_child_files(folder_path)
        images: list[str] = []
        poster_path: str | None = None

        for item in items:
            full_path = self._normalize_path(item.full_path)
            base_name = Path(item.name).stem

            if not full_path or not os.path.isfile(full_path):
                continue

            if not self.is_image_file(full_path):
                continue

            images.append(full_path)
            if poster_path is None and base_name.endswith("poster"):
                poster_path = full_path

        return images, poster_path

    def build_folder_item(self, path: str, depth: int = 0) -> FileUtilModel:
        path = self._normalize_path(path)
        return FileUtilModel(
            type="dir",
            name=Path(path).name,
            full_path=path,
            depth=depth,
        )

    def build_file_item(self, path: str, depth: int = 0) -> FileUtilModel:
        path = self._normalize_path(path)
        name = Path(path).name
        file_type = self.classify_file(name)
        return FileUtilModel(
            type="file",
            name=name,
            full_path=path,
            depth=depth,
            file_type=file_type,
        )

    def classify_file(self, name: str) -> str | None:
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

    def is_nfo_file(self, path: str) -> bool:
        path = self._normalize_path(path)
        return bool(path) and Path(path).suffix.casefold() in self.NFO_EXTS

    def is_video_file(self, path: str) -> bool:
        path = self._normalize_path(path)
        return bool(path) and Path(path).suffix.casefold() in self.VIDEO_EXTS

    def is_image_file(self, path: str) -> bool:
        path = self._normalize_path(path)
        return bool(path) and Path(path).suffix.casefold() in self.IMAGE_EXTS

    def find_first_file_by_extensions(self, path: str, exts: set[str]) -> str | None:
        path = self._normalize_path(path)
        if not path or not os.path.isdir(path):
            return None

        sorted_entries = self._safe_scandir(path)
        if sorted_entries is None:
            return None

        for entry in sorted_entries:
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                if Path(entry.name).suffix.casefold() in exts:
                    return self._normalize_path(entry.path)
            except (OSError, PermissionError):
                continue

        return None

    def find_nfo_file(self, path: str) -> str | None:
        path = self._normalize_path(path)
        if not path or not os.path.isdir(path):
            return None

        preferred_names = ("movie.nfo", "tvshow.nfo")
        entries_list = self._safe_scandir(path)
        if entries_list is None:
            return None

        for preferred_name in preferred_names:
            for entry in entries_list:
                try:
                    if entry.name.casefold() == preferred_name and entry.is_file(
                        follow_symlinks=False
                    ):
                        return self._normalize_path(entry.path)
                except (OSError, PermissionError):
                    continue

        for entry in entries_list:
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                if Path(entry.name).suffix.casefold() in self.NFO_EXTS:
                    return self._normalize_path(entry.path)
            except (OSError, PermissionError):
                continue

        return None
