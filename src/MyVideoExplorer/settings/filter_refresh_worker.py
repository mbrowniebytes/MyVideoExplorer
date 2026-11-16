from __future__ import annotations

import logging
import time

from PySide6.QtCore import QThread, Signal

from MyVideoExplorer.db.db_filters import DbFilters

logger = logging.getLogger(__name__)


class FilterRefreshWorker(QThread):
    """Refresh saved filters without blocking the GUI thread.

    Processes filters sequentially with a small delay between operations to ensure
    DuckDB connections are fully closed before the next refresh, preventing
    "filter_catalog.db not able to write" errors.
    """

    progress = Signal(int, int, str)
    updated = Signal(str)
    failed = Signal(str, str)

    def __init__(self, filter_store: DbFilters, names: list[str]) -> None:
        super().__init__()
        self.filter_store = filter_store
        self.names = names

    def run(self) -> None:
        total = len(self.names)
        for index, name in enumerate(self.names, start=1):
            self.progress.emit(index, total, name)
            try:
                self.filter_store.refresh_filter(name)
            except Exception as error:
                logger.exception("Failed refreshing saved filter %s", name)
                self.failed.emit(name, str(error))
            else:
                self.updated.emit(name)
            # Small delay to ensure DuckDB connection is fully released before next refresh
            if index < total:
                time.sleep(0.05)
