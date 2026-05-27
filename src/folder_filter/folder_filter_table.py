from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QToolButton,
    QSizePolicy,
)

from src.theme.theme import APP_THEME


class FolderFilterTable(QTableWidget):
    """
    Table widget for displaying and editing folder filters.
    """

    FILTER_TYPES = [
        "OS",
        "Folder",
        "File",
        # TODO re-enable once have a db
        # "NFO",
        # "Genre",
        # "Actor",
        # "Director",
        # "Title",
        # "Plot",
    ]

    sig_genre_changed = Signal(str)
    sig_root_folder = Signal(str)

    def __init__(self, genres: list[str], folder_configs: list[dict]):
        super().__init__()
        self.genres = genres
        self.folder_configs = folder_configs
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.verticalHeader().setVisible(False)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Filter", "Value", ""])
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.setStyleSheet(APP_THEME.table_qss())

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        self._check_empty_state()

    def _check_empty_state(self) -> None:
        if self.rowCount() == 0:
            self.insertRow(0)
            placeholder = QTableWidgetItem("Add a Filter from above dropdown")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(0, 0, placeholder)
            self.setSpan(0, 0, 1, 3)
        elif self.rowCount() > 1 and self.columnSpan(0, 0) > 1:
            # Remove placeholder if we have more than 1 row and 0,0 is spanned
            self.removeRow(0)
        elif self.rowCount() == 1 and self.columnSpan(0, 0) > 1:
            # This is the placeholder row, do nothing
            pass

        self._update_height()

    def _update_height(self) -> None:
        header_height = self.horizontalHeader().height()
        rows_height = 0
        for i in range(self.rowCount()):
            rows_height += self.rowHeight(i)

        total_height = header_height + rows_height + 6  # +6 for borders
        self.setFixedHeight(total_height)

    def add_filter(self, filter_type: str, filter_value: str = "") -> None:
        if self.rowCount() == 1 and self.columnSpan(0, 0) > 1:
            self.removeRow(0)

        filter_type.casefold().strip()
        row_nbr = self.rowCount()
        self.insertRow(row_nbr)
        self._set_filter_type_cell(row_nbr, filter_type)
        self._set_filter_value_cell(row_nbr, filter_type, filter_value)
        self._set_remove_button_cell(row_nbr)
        self._update_height()

    def _set_filter_type_cell(self, row_nbr: int, filter_type: str) -> None:
        clean_type = filter_type.casefold().strip()
        if clean_type in ("os", "nfo"):
            label_text = filter_type.strip()
        else:
            label_text = f"  {filter_type.strip()}"
        filter_type_label = QTableWidgetItem(label_text)
        if clean_type in ("os", "nfo"):
            filter_type_label.setFlags(Qt.ItemFlag.NoItemFlags)
        else:
            filter_type_label.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )
        filter_type_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
        self.setItem(row_nbr, 0, filter_type_label)

    def _set_filter_value_cell(
        self, row_nbr: int, filter_type: str, filter_value: str = ""
    ) -> None:
        clean_type = filter_type.casefold().strip()
        if clean_type == "genre":
            # For Genre, we use a new combo box
            combo = QComboBox()
            combo.addItem("-none-")
            for genre in self.genres:
                combo.addItem(genre)
            if filter_value:
                combo.setCurrentText(filter_value)
            APP_THEME.setup_combo_box(combo)
            combo.currentTextChanged.connect(self.sig_genre_changed.emit)
            self.setCellWidget(row_nbr, 1, combo)
            return

        if clean_type == "media":
            # For Media, we use a new combo box
            combo = QComboBox()
            combo.addItem("- Select Folder -", userData="")
            for config in self.folder_configs:
                combo.addItem(config["label"], userData=config["path"])
            if filter_value:
                # Try to find by text first, then by data if that fails
                index = combo.findText(filter_value)
                if index == -1:
                    index = combo.findData(filter_value)
                if index != -1:
                    combo.setCurrentIndex(index)
            APP_THEME.setup_combo_box(combo)
            combo.currentIndexChanged.connect(
                lambda idx: (
                    self.sig_root_folder.emit(combo.itemData(idx)) if idx > 0 else None
                )
            )
            self.setCellWidget(row_nbr, 1, combo)
            return

        filter_type_value = QTableWidgetItem(filter_value)
        if filter_type.upper() in ("OS", "NFO"):
            filter_type_value.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )
        else:
            filter_type_value.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
            )

        filter_type_value.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
        self.setItem(row_nbr, 1, filter_type_value)

    def _set_remove_button_cell(self, row_nbr: int) -> None:

        remove_btn = QToolButton()
        remove_btn.setIcon(APP_THEME.icon("fa5s.times", color=APP_THEME.text_color))
        remove_btn.setToolTip("Remove filter")
        remove_btn.setStyleSheet(APP_THEME.small_button_qss())
        remove_btn.clicked.connect(lambda: self._remove_filter_row(remove_btn))
        self.setCellWidget(row_nbr, 2, remove_btn)

    def _remove_filter_row(self, btn: QToolButton) -> None:
        row = self.indexAt(btn.pos()).row()
        if row >= 0:
            self.removeRow(row)
            self._check_empty_state()

    def collect_filters(self) -> list[dict[str, str]]:
        filters: list[dict[str, str]] = []

        if self.rowCount() == 1 and self.columnSpan(0, 0) > 1:
            return filters

        for row in range(self.rowCount()):
            filter_type_raw = self._filter_type_at(row)
            if not filter_type_raw:
                continue

            # Find the original case from FILTER_TYPES
            filter_type = next(
                (ft for ft in self.FILTER_TYPES if ft.casefold() == filter_type_raw),
                filter_type_raw,
            )

            filter_value = self._filter_value_at(row, filter_type_raw)
            if filter_value:
                filters.append({"filter": filter_type, "value": filter_value})

        return filters

    def _filter_type_at(self, row: int) -> str:
        filter_item = self.item(row, 0)
        if filter_item is None:
            return ""
        return filter_item.text().casefold().strip()

    def _filter_value_at(self, row: int, filter_type: str) -> str:
        widget = self.cellWidget(row, 1)
        if isinstance(widget, QComboBox):
            if filter_type == "genre":
                return (
                    ""
                    if widget.currentIndex() <= 0
                    else widget.currentText().casefold().strip()
                )
            if filter_type == "media":
                return (
                    ""
                    if widget.currentIndex() <= 0
                    else widget.currentText().casefold().strip()
                )

        value_item = self.item(row, 1)
        return value_item.text().strip() if value_item else ""

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.table_qss())
