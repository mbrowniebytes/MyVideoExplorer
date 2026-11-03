from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from MyVideoExplorer.db.db_filters import DbFilters

logger = logging.getLogger(__name__)


class FilterScanWorker(QThread):
    """Validate manual entries after a media library scan."""

    updated = Signal(list)
    failed = Signal(str)

    def __init__(self, filter_store: DbFilters, media_folder: str) -> None:
        super().__init__()
        self.filter_store = filter_store
        self.media_folder = media_folder

    def run(self) -> None:
        try:
            names = self.filter_store.mark_manual_items_stale(self.media_folder)
        except Exception as error:
            logger.exception(
                "Failed validating manual filters after scan of %s",
                self.media_folder,
            )
            self.failed.emit(str(error))
        else:
            self.updated.emit(names)
