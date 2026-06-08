from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.utils.file_util_model import FileUtilModel
from src.utils.log_util import LogUtil
from src.utils.file_util_type import FileUtilType


class FileUtil:
    """Utility class for filesystem traversal, classification, and metadata extraction."""


    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util
        self.file_type = FileUtilType()

        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _scan_directory(self, path: Path) -> list[os.DirEntry[str]]:
        """Safely scan a directory and return entries sorted by name."""
        try:
            return sorted(os.scandir(path), key=lambda e: e.name)
        except OSError as e:
            if self.log_util:
                self.log_util.error(f"Failed to scan directory {path}: {e}")
            return []

    def list_directory(self, path: str) -> list[FileUtilModel]:
        """Return direct children for a folder, sorted by name."""
        target = Path(path)
        if not target.is_dir():
            return []

        items: list[FileUtilModel] = []
        for entry in self._scan_directory(target):
            try:
                if entry.is_dir(follow_symlinks=False):
                    items.append(self.build_folder_item(entry.path, depth=0))
                elif entry.is_file(follow_symlinks=False):
                    items.append(self.build_file_item(entry.path, depth=0))
            except OSError:
                continue
        return items

    def get_child_dirs(self, path: str) -> list[FileUtilModel]:
        """Return only directory children of a path."""
        return [item for item in self.list_directory(path) if item.is_dir]

    def get_child_files(self, path: str) -> list[FileUtilModel]:
        """Return only file children of a path."""
        return [item for item in self.list_directory(path) if item.is_file]

    def get_files_from_path(self, path: str, depth: int = 0) -> list[FileUtilModel]:
        """Recursively collect directory and file metadata for a path."""
        target = Path(path)
        if not target.is_dir():
            return []

        items: list[FileUtilModel] = []
        for entry in self._scan_directory(target):
            try:
                if entry.is_dir(follow_symlinks=False):
                    items.append(self.build_folder_item(entry.path, depth=depth))
                    items.extend(self.get_files_from_path(entry.path, depth + 1))
                elif entry.is_file(follow_symlinks=False):
                    items.append(self.build_file_item(entry.path, depth=depth))
            except OSError:
                continue
        return items

    def get_images_from_folder(self, folder_path: str) -> tuple[list[str], str | None]:
        """Return all image paths and the first poster image path if found."""
        target = Path(folder_path)
        if not target.is_dir():
            # print(f"get_images_from_folder: target: {target}")
            return [], None

        images: list[str] = []
        poster_path: str | None = None

        for entry in self._scan_directory(target):
            # print(f"get_images_from_folder: entry.path: {entry.path}")
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                if self.is_image_file(entry.path):
                    images.append(entry.path)
                    if poster_path is None and Path(entry.name).stem.casefold().endswith("poster"):
                        poster_path = entry.path
            except OSError:
                continue

        return images, poster_path

    def build_folder_item(self, path: str, depth: int = 0) -> FileUtilModel:
        """Construct a FileUtilModel representing a directory."""
        target = Path(path)
        return FileUtilModel(
            type="dir",
            name=target.name,
            full_path=str(target),
            depth=depth,
        )

    def build_file_item(self, path: str, depth: int = 0) -> FileUtilModel:
        """Construct a FileUtilModel representing a file."""
        target = Path(path)
        return FileUtilModel(
            type="file",
            name=target.name,
            full_path=str(target),
            depth=depth,
            file_type=self.classify_file(target.name),
        )

    def classify_file(self, name: str) -> str | None:
        return self.file_type.classify(name)

    def is_nfo_file(self, path: str) -> bool:
        return self.file_type.is_nfo_file(path)

    def is_video_file(self, path: str) -> bool:
        return self.file_type.is_video_file(path)

    def is_image_file(self, path: str) -> bool:
        return self.file_type.is_image_file(path)

    def find_first_file_by_extensions(self, path: str, exts: set[str]) -> str | None:
        """Find the first file in a directory matching any of the given extensions."""
        target = Path(path)
        if not target.is_dir():
            return None

        for entry in self._scan_directory(target):
            try:
                if entry.is_file(follow_symlinks=False) and Path(entry.name).suffix.casefold() in exts:
                    return entry.path
            except OSError:
                continue
        return None

    def find_nfo_file(self, path: str) -> str | None:
        """Locate an NFO file, prioritizing standard media naming conventions."""
        target = Path(path)
        if not target.is_dir():
            return None

        preferred_names = {"movie.nfo", "tvshow.nfo"}
        entries = self._scan_directory(target)

        # First pass: prioritize standard media NFO names
        for entry in entries:
            try:
                if entry.is_file(follow_symlinks=False) and entry.name.casefold() in preferred_names:
                    return entry.path
            except OSError:
                continue

        # Second pass: fallback to any file with NFO extension
        for entry in entries:
            try:
                if entry.is_file(follow_symlinks=False) and self.file_type.is_nfo_file(entry.name):
                    return entry.path
            except OSError:
                continue
        return None
