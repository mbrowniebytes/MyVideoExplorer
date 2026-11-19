from __future__ import annotations

import logging
from pathlib import Path
from typing import TypeVar

import msgspec
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=msgspec.Struct)


class SettingsImportWorker(QThread):
    """Import settings data from a JSON file without blocking the GUI thread.

    Reads and parses a JSON file, then validates it using msgspec schema-based
    decoding. Emits the parsed data on success for the caller to process.
    """

    progress = Signal(int, int, str)
    validated = Signal(int)
    data_ready = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        file_path: Path,
        decode_type: type[T],
    ) -> None:
        super().__init__()
        self._file_path = file_path
        self._decode_type = decode_type

    def run(self) -> None:
        try:
            self.progress.emit(0, 2, "Reading file...")
            if not self._file_path.exists():
                self.failed.emit(f"File not found: {self._file_path.name}")
                return
            raw = self._file_path.read_bytes()
            self.progress.emit(1, 2, "Parsing JSON...")
            try:
                data = msgspec.json.decode(raw, type=self._decode_type)
            except msgspec.DecodeError as exc:
                self.failed.emit(f"Invalid data format: {exc}")
                return

            self.validated.emit(1)
            self.data_ready.emit(data)
            self.progress.emit(2, 2, "Import validation complete.")
            self.finished.emit()
        except Exception as exc:
            logger.exception("Import failed")
            self.failed.emit(str(exc))
