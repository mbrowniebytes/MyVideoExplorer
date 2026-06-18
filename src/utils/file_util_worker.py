from __future__ import annotations

from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from src.utils.file_util import FileUtil


class FileUtilWorker(QObject):
    finished = Signal(list)

    def __init__(self, file_util: FileUtil, path: str, depth: int = 0):
        super().__init__()
        self.file_util = file_util
        self.path = path
        self.depth = depth

    def run(self):
        # We need a dummy callback for _get_files_from_path,
        # but it's not strictly required if we just return the result
        items = self.file_util._get_files_from_path(self.path, self.depth)
        self.finished.emit(items)
