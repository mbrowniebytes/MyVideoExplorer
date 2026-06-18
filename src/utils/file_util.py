from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from collections.abc import Callable
from time import sleep

from PySide6.QtCore import QThread

from src.utils.file_util_model import FileUtilModel
from src.utils.file_util_worker import FileUtilWorker
from src.utils.log_util import LogUtil
from src.utils.file_util_type import FileUtilType
from src.app.app_environment import IS_DEVELOPMENT




class FileUtil:
    """Utility class for filesystem traversal, classification, and metadata extraction."""

    @staticmethod
    def get_resource_path(relative_path: str) -> str:
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def __init__(self, log_util: LogUtil) -> None:
        self.log_util = log_util
        self.file_type = FileUtilType()
        self._scan_lock = threading.Lock()
        self.active_tasks: list[dict] = []

        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _scan_directory(self, path: Path) -> list[os.DirEntry[str]]:
        """Safely scan a directory and return entries sorted by name."""
        try:
            with self._scan_lock:
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

    def _get_files_from_path(
        self,
        path: str,
        depth: int = 0,
        callback: Callable[[list[FileUtilModel]], None] | None = None
    ) -> list[FileUtilModel]:
        """Asynchronously collect directory and file metadata for a path."""
        target = Path(path)
        if not target.is_dir():
            return []

        items: list[FileUtilModel] = []
        for entry in self._scan_directory(target):
            try:
                # dev test large qty folders
                if IS_DEVELOPMENT:
                    sleep(0.001)
                if entry.is_dir(follow_symlinks=False):
                    folder_item = self.build_folder_item(entry.path, depth=depth)
                    items.append(folder_item)
                    # Recursively get files from subdirectory
                    sub_items = self._get_files_from_path(
                        entry.path,
                        depth + 1,
                        callback
                    )
                    items.extend(sub_items)
                elif entry.is_file(follow_symlinks=False):
                    items.append(self.build_file_item(entry.path, depth=depth))
            except OSError:
                continue

        if callback:
            callback(items)

        return items

    def get_files_from_path_async(
        self,
        path: str,
        depth: int = 0,
        on_complete: Callable[[list[FileUtilModel]], None] | None = None
    ) -> None:
        """Asynchronously collect directory and file metadata for a path."""
        thread = QThread()
        worker = FileUtilWorker(self, path, depth)
        worker.moveToThread(thread)

        task = {"thread": thread, "worker": worker}
        with self._scan_lock:
            self.active_tasks.append(task)

        thread.started.connect(worker.run)
        worker.finished.connect(
            lambda items: self._on_finished(items, on_complete, thread, worker)
        )
        thread.start()

    def _on_finished(
        self,
        items: list[FileUtilModel],
        on_complete: Callable[[list[FileUtilModel]], None] | None,
        thread: QThread,
        worker: FileUtilWorker,
    ):
        thread.quit()
        thread.wait()

        with self._scan_lock:
            self.active_tasks = [
                t for t in self.active_tasks if t["thread"] != thread
            ]

        if on_complete:
            on_complete(items)

    def get_images_from_folder(self, folder_path: str) -> tuple[list[str], str | None]:
        """Return all image paths and the first poster image path if found."""
        target = Path(folder_path)
        if not target.is_dir():
            # print(f"get_images_from_folder: target: {target}")
            return [], None

        posters = []
        fanarts = []
        others = []

        for entry in self._scan_directory(target):
            try:
                if not entry.is_file(follow_symlinks=False):
                    continue
                if self.is_image_file(entry.path):
                    stem = Path(entry.name).stem.casefold()
                    if stem.endswith("poster"):
                        posters.append(entry.path)
                    elif stem.endswith("fanart"):
                        fanarts.append(entry.path)
                    else:
                        others.append(entry.path)
            except OSError:
                continue

        images = posters + fanarts + others
        posters.sort(key=lambda p: len(Path(p).stem))
        poster_path = posters[0] if posters else None

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
