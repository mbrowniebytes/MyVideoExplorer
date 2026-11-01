from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from MyVideoExplorer.db.db_filters import DbFilters

logger = logging.getLogger(__name__)


class FilterCountWorker(QThread):
    """Refresh saved-filter counts without blocking the GUI thread."""

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
                self.filter_store.refresh_filter_counts(name)
            except Exception as error:
                logger.exception("Failed refreshing movie count for filter %s", name)
                self.failed.emit(name, str(error))
            else:
                self.updated.emit(name)
