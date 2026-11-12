from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.compare.compare_model import COMPARE_COLUMNS, CompareTableModel
from MyVideoExplorer.compare.compare_worker import CompareWorker
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.combo_boxes.checkbox_combo_box import CheckboxComboBox
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox

if TYPE_CHECKING:
    from MyVideoExplorer.settings.settings_state import SettingsState
    from MyVideoExplorer.utils.file_util import FileUtil


class CompareTab(SettingsBaseTab):
    """UI widget for the Compare sub-tab in Settings > Media."""

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        file_util: FileUtil,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the compare tab.

        Args:
            state: Settings state (provides media configs).
            log_util: Logging utility.
            file_util: File utility.
            parent: Qt parent widget.
        """
        super().__init__(log_util, parent)
        self._state = state
        self._file_util = file_util
        self._compare_dbs: dict[str, Path] = {}
        self._worker: CompareWorker | None = None
        self._model: CompareTableModel | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the compare tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # First row: Compare media with Load DB button
        compare_row = QHBoxLayout()
        compare_row.setSpacing(10)
        compare_row.addStretch()

        self._compare_db_label = QLabel("Compare media:")
        self._compare_db_combo = SelectComboBox()
        self._compare_db_combo.setPlaceholderText("Load DB first")
        self._compare_db_combo.setEnabled(False)

        self._import_btn = QPushButton("Load DB")
        self._import_btn.clicked.connect(self._on_import_db)

        compare_row.addWidget(self._compare_db_label)
        compare_row.addWidget(self._compare_db_combo, 1)
        compare_row.addWidget(self._import_btn)
        layout.addLayout(compare_row)

        # Second row: Local media with Compare button
        local_row = QHBoxLayout()
        local_row.setSpacing(10)
        local_row.addStretch()

        self._local_db_label = QLabel("Local media:")
        self._local_db_combo = SelectComboBox()
        self._local_db_combo.setPlaceholderText("Select local media")

        self._compare_btn = QPushButton("Compare")
        self._compare_btn.clicked.connect(self._on_compare)
        self._compare_btn.setEnabled(False)

        local_row.addWidget(self._local_db_label)
        local_row.addWidget(self._local_db_combo, 1)
        local_row.addWidget(self._compare_btn)
        layout.addLayout(local_row)

        self._local_db_combo.currentIndexChanged.connect(self._on_local_db_changed)
        self._compare_db_combo.currentIndexChanged.connect(self._on_compare_db_changed)

        # Populate database selectors
        self._populate_local_db_combo()
        self._populate_compare_db_combo()

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        self._status_label = QLabel("Status:")
        self._status_checkbox = CheckboxComboBox(self)
        self._status_checkbox.set_items(["missing", "match", "similar"])
        self._status_checkbox.selection_changed.connect(self._on_status_changed)

        self._search_label = QLabel("Search:")
        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Search all columns...")
        self._search_field.returnPressed.connect(self._on_search_changed)

        filter_layout.addWidget(self._status_label)
        filter_layout.addWidget(self._status_checkbox.widget)
        filter_layout.addStretch()
        filter_layout.addWidget(self._search_label)
        filter_layout.addWidget(self._search_field, 1)
        layout.addLayout(filter_layout)

        # Table section
        self._table_view = QTableView()
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSortingEnabled(True)
        self._table_view.setStyleSheet(APP_THEME.table_qss())
        header = self._table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for i, col in enumerate(COMPARE_COLUMNS):
            width = int(col["width"])
            header.setDefaultSectionSize(width)
            if col["key"] == "row_number":
                header.setMinimumSectionSize(40)
            elif col["key"] == "match_score":
                header.setMinimumSectionSize(80)
        layout.addWidget(self._table_view, 1)

        # Pagination section
        page_layout = QHBoxLayout()
        page_layout.setSpacing(10)

        self._prev_btn = QPushButton("Previous")
        self._prev_btn.clicked.connect(self._on_prev_page)
        self._prev_btn.setEnabled(False)

        self._page_label = QLabel("Page 0 / 0")

        self._next_btn = QPushButton("Next")
        self._next_btn.clicked.connect(self._on_next_page)
        self._next_btn.setEnabled(False)

        page_layout.addWidget(self._prev_btn)
        page_layout.addWidget(self._page_label, 1)
        page_layout.addWidget(self._next_btn)
        layout.addLayout(page_layout)

    def _get_selected_local_db_path(self) -> Path | None:
        """Get the DB path for the currently selected local media config.

        Returns:
            Path to the local database, or None if not selected.
        """
        data = self._local_db_combo.currentData()
        if data:
            return Path(data)
        return None

    def _get_selected_compare_db_path(self) -> Path | None:
        """Get the DB path for the currently selected compare database.

        Returns:
            Path to the compare database, or None if not selected.
        """
        data = self._compare_db_combo.currentData()
        if data:
            return Path(data)
        return None

    def _populate_local_db_combo(self) -> None:
        """Populate the local media combo box with all media configs."""
        current = self._local_db_combo.currentData()
        self._local_db_combo.clear()
        self._local_db_combo.addItem("", None)

        for config in self._state.media_configs:
            label = config.get("label", "")
            path = config.get("path", "")
            db_path = self._state.get_db_path(config)
            if label and path:
                display = f"{label}:{path}"
                self._local_db_combo.addItem(display, db_path)

        if current:
            idx = self._local_db_combo.findData(current)
            if idx >= 0:
                self._local_db_combo.setCurrentIndex(idx)

    def _populate_compare_db_combo(self) -> None:
        """Populate the compare media combo box with loaded compare databases."""
        current = self._compare_db_combo.currentData()
        self._compare_db_combo.clear()
        self._compare_db_combo.addItem("", None)

        # Scan for existing compare DBs in the tmp directory
        tmp_dir = Path("tmp")
        if tmp_dir.exists():
            for db_file in sorted(tmp_dir.glob("compare_*.db")):
                # Extract the media name from the filename
                media_name = db_file.stem.replace("compare_", "", 1)
                display = f"{media_name}:{db_file}"
                self._compare_db_combo.addItem(display, str(db_file))
                self._compare_dbs[media_name] = db_file

        if self._compare_dbs:
            self._compare_db_combo.setEnabled(True)

        if current:
            idx = self._compare_db_combo.findData(current)
            if idx >= 0:
                self._compare_db_combo.setCurrentIndex(idx)

    def _on_local_db_changed(self) -> None:
        """Handle local media database selection change."""
        self._update_compare_button_state()

    def _on_compare_db_changed(self) -> None:
        """Handle compare media database selection change."""
        self._update_compare_button_state()

    def _update_compare_button_state(self) -> None:
        """Enable/disable the compare button based on selections."""
        local_ok = self._get_selected_local_db_path() is not None
        compare_ok = self._get_selected_compare_db_path() is not None
        self._compare_btn.setEnabled(local_ok and compare_ok)

    def _on_import_db(self) -> None:
        """Handle import database button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Compare Database",
            "",
            "DuckDB Files (*.db);;All Files (*)",
        )
        if not file_path:
            return

        try:
            media_name = Path(file_path).stem
            from MyVideoExplorer.compare.compare_service import CompareService

            service = CompareService(Path())
            dest = service.import_compare_db(Path(file_path), media_name)
            self._compare_dbs[media_name] = dest
            self._populate_compare_db_combo()
            # Auto-select the newly imported database
            idx = self._compare_db_combo.findData(str(dest))
            if idx >= 0:
                self._compare_db_combo.setCurrentIndex(idx)
            self._update_compare_button_state()
            if self.log_util:
                self.log_util.info(f"Imported compare database: {dest}")
        except Exception as e:
            if self.log_util:
                self.log_util.error(f"Failed to import database: {e}")

    def _on_compare(self) -> None:
        """Handle compare button click."""
        local_db = self._get_selected_local_db_path()
        compare_db = self._get_selected_compare_db_path()
        if local_db is None or compare_db is None:
            return

        self._progress_bar.setVisible(True)
        self._progress_bar.setRange(0, 0)
        self._compare_btn.setEnabled(False)

        self._worker = CompareWorker(
            local_db,
            compare_db,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        """Handle progress signal."""
        self._progress_bar.setFormat(message)

    def _on_finished(self, count: int) -> None:
        """Handle comparison finished signal."""
        self._progress_bar.setVisible(False)
        self._compare_btn.setEnabled(True)

        compare_db = self._get_selected_compare_db_path()
        if compare_db:
            self._model = CompareTableModel(compare_db, self)
            self._table_view.setModel(self._model)
            self._update_pagination()
            if self.log_util:
                self.log_util.info(f"Comparison complete: {count} results")

    def _on_failed(self, error: str) -> None:
        """Handle comparison failed signal."""
        self._progress_bar.setVisible(False)
        self._compare_btn.setEnabled(True)
        if self.log_util:
            self.log_util.error(f"Comparison failed: {error}")

    def _on_status_changed(self, selected: list[str]) -> None:
        """Handle status filter change (multi-select)."""
        if self._model:
            self._model.set_status_filters(selected)
            self._update_pagination()

    def _on_search_changed(self) -> None:
        """Handle search field change."""
        if self._model:
            query = self._search_field.text().strip()
            self._model.set_search_query(query)
            self._update_pagination()

    def _on_prev_page(self) -> None:
        """Handle previous page button click."""
        if self._model and self._model.prev_page():
            self._update_pagination()

    def _on_next_page(self) -> None:
        """Handle next page button click."""
        if self._model and self._model.next_page():
            self._update_pagination()

    def _update_pagination(self) -> None:
        """Update pagination controls."""
        if self._model:
            current, total = self._model.page_info()
            self._page_label.setText(f"Page {current + 1} / {total}")
            self._prev_btn.setEnabled(current > 0)
            self._next_btn.setEnabled(current + 1 < total)
