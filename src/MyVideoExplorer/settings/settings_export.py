from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import msgspec
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SettingsExportWorker(QThread):
    """Export settings data to a JSON file without blocking the GUI thread.

    Accepts a callable that returns the data to export and writes it to the
    specified file path using atomic writes.
    """

    progress = Signal(int, int, str)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, get_data: Callable[[], dict[str, Any]], file_path: Path) -> None:
        super().__init__()
        self._get_data = get_data
        self._file_path = file_path

    def run(self) -> None:
        try:
            self.progress.emit(0, 2, "Collecting data...")
            data = self._get_data()
            self.progress.emit(1, 2, "Writing file...")
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self._file_path.parent / f".{self._file_path.name}.tmp"
            raw = msgspec.json.encode(data)
            formatted = msgspec.json.format(raw, indent=4)
            temp_path.write_bytes(formatted)
            temp_path.replace(self._file_path)
            self.progress.emit(2, 2, "Export complete.")
            self.finished.emit()
        except Exception as exc:
            logger.exception("Export failed")
            self.failed.emit(str(exc))
            temp_path = self._file_path.parent / f".{self._file_path.name}.tmp"
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
