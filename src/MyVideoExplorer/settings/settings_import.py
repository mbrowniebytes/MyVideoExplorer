from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class SettingsImportWorker(QThread):
    """Import settings data from a JSON file without blocking the GUI thread.

    Reads and parses a JSON file, then validates it using a caller-provided
    validation callback. Emits the parsed data on success for the caller to
    process.
    """

    progress = Signal(int, int, str)
    validated = Signal(int)
    data_ready = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        file_path: Path,
        validate: Callable[[dict[str, Any]], list[str]],
    ) -> None:
        super().__init__()
        self._file_path = file_path
        self._validate = validate

    def run(self) -> None:
        try:
            self.progress.emit(0, 2, "Reading file...")
            if not self._file_path.exists():
                self.failed.emit(f"File not found: {self._file_path.name}")
                return
            raw = self._file_path.read_text(encoding="utf-8")
            self.progress.emit(1, 2, "Parsing JSON...")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                self.failed.emit(f"Invalid JSON: {exc}")
                return

            self.progress.emit(1, 2, "Validating...")
            errors = self._validate(data)
            if errors:
                self.failed.emit("\n".join(errors))
                return

            self.validated.emit(1)
            self.data_ready.emit(data)
            self.progress.emit(2, 2, "Import validation complete.")
            self.finished.emit()
        except Exception as exc:
            logger.exception("Import failed")
            self.failed.emit(str(exc))
