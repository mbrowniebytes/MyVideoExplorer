from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from MyVideoExplorer.compare.compare_service import CompareService


class CompareWorker(QThread):
    """Background worker for running media comparisons."""

    progress = Signal(int, int, str)
    finished = Signal(int)
    failed = Signal(str)

    def __init__(
        self,
        local_db_path: Path,
        compare_db_path: Path,
    ) -> None:
        """Initialize the compare worker.

        Args:
            local_db_path: Path to the local DuckDB database.
            compare_db_path: Path to the imported compare database.
        """
        super().__init__()
        self._local_db_path = local_db_path
        self._compare_db_path = compare_db_path

    def run(self) -> None:
        """Execute the comparison in the background."""
        try:
            self.progress.emit(0, 1, "Loading local database...")
            service = CompareService()
            count = service.run_comparison(
                self._local_db_path,
                self._compare_db_path,
            )
            self.progress.emit(1, 1, "Comparison complete.")
            self.finished.emit(count)
        except Exception as e:
            self.failed.emit(str(e))
