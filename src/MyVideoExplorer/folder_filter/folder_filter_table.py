from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QSize, Qt, Signal

if TYPE_CHECKING:
    from MyVideoExplorer.db.db_tags import DbTags
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.folder_filter.filter_last_played_widget import (
    FilterLastPlayedWidget,
)
from MyVideoExplorer.folder_filter.filter_qty_played_widget import (
    FilterQtyPlayedWidget,
)
from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_util import get_contrast_text_color
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.flow_layout import FlowLayout


class FilterTagCloudWidget(QWidget):
    """
    Inline tag cloud widget used in FolderFilterTable value cells for Tag filter type.
    Displays selected tags as pills and provides inline add/remove in editable mode.
    """

    def __init__(
        self,
        table: FolderFilterTable,
        readonly: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent or table)
        self.table = table
        self.readonly = readonly
        self._tags: list[str] = []
        self._layout = FlowLayout(self, spacing=4)
        self._layout.setContentsMargins(4, 3, 4, 3)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )

    @property
    def row(self) -> int:
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 1) is self:
                return r
        return -1

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._layout.heightForWidth(width)

    def sizeHint(self) -> QSize:
        w = 0
        if self.table is not None:
            w = self.table.columnWidth(1)
            if self.table.viewport().width() > 100:
                calc_w = (
                    self.table.viewport().width()
                    - self.table.columnWidth(0)
                    - (self.table.columnWidth(2) if not self.readonly else 0)
                )
                if calc_w > 50:
                    w = calc_w
        if w <= 50:
            w = self.width()
        if w <= 50:
            w = 200
        h = self._layout.heightForWidth(w)
        return QSize(w, max(h, 28))

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout.setGeometry(self.rect())
        r = self.row
        if r >= 0 and self.table is not None:
            target_h = max(self.sizeHint().height(), 32)
            if self.table.rowHeight(r) != target_h:
                self.table.setRowHeight(r, target_h)
                self.table._update_height()

    def get_tags(self) -> list[str]:
        return list(self._tags)

    def set_tags(self, tags: list[str]) -> None:
        seen = set()
        cleaned: list[str] = []
        for t in tags:
            s = str(t).strip()
            if s and s != "- Select Tag -" and s.casefold() not in seen:
                seen.add(s.casefold())
                cleaned.append(s)
        self._tags = cleaned
        self.refresh()
        r = self.row
        if r >= 0:
            target_h = max(self.sizeHint().height(), 32)
            self.table.setRowHeight(r, target_h)
            self.table._update_height()
            self._layout.setGeometry(self.rect())

    def add_tag(self, tag: str, emit_signal: bool = True) -> None:
        s = str(tag).strip()
        if not s or s == "- Select Tag -":
            return
        if s.casefold() not in {t.casefold() for t in self._tags}:
            self._tags.append(s)
            self.refresh()
            r = self.row
            if r >= 0:
                target_h = max(self.sizeHint().height(), 32)
                self.table.setRowHeight(r, target_h)
                self.table._update_height()
                self._layout.setGeometry(self.rect())
                if emit_signal:
                    self.table.cellChanged.emit(r, 1)

    def remove_tag(self, tag: str) -> None:
        self._tags = [t for t in self._tags if t.casefold() != tag.casefold()]
        self.refresh()
        r = self.row
        if r >= 0:
            target_h = max(self.sizeHint().height(), 32)
            self.table.setRowHeight(r, target_h)
            self.table._update_height()
            self._layout.setGeometry(self.rect())
            self.table.cellChanged.emit(r, 1)

    def open_picker(self) -> None:
        self.table._open_tag_picker(self, self)

    def refresh(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        for tag in self._tags:
            color, count = self.table._get_tag_info(tag)
            btn = TagButton(self)
            btn.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
            if self.readonly:
                btn.setText(f"{tag} ({count})")
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
                btn.setToolTip(tag)
                btn.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                btn.setText(f"{tag} ({count})  ✕")
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
                btn.setToolTip(f"Remove tag '{tag}'")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _, t=tag: self.remove_tag(t))

            btn.setStyleSheet(
                f"QToolButton {{ color: {get_contrast_text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 6px; font-weight: bold; border: 0; }}"
            )
            btn.show()
            self._layout.addWidget(btn)

        if not self.readonly:
            add_btn = QToolButton(self)
            add_btn.setIcon(APP_THEME.icon("fa6s.tag", color=APP_THEME.text_color))
            add_btn.setIconSize(QSize(12, 12))
            add_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            add_btn.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
            add_btn.setToolTip("Add Tag to filter")
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setProperty("preserve_custom_style", True)
            add_btn.setStyleSheet(
                f"QToolButton {{ "
                f"color: {APP_THEME.text_color}; "
                f"background-color: {APP_THEME.surface_color}; "
                f"border: 1px solid {APP_THEME.border_color}; "
                f"border-radius: 4px; "
                f"padding: 2px 6px; "
                f"}} "
                f"QToolButton:hover {{ "
                f"background-color: {APP_THEME.config.color_interaction_hover}; "
                f"border: 1px solid {APP_THEME.config.color_interaction_selected}; "
                f"}}"
            )
            add_btn.clicked.connect(self.open_picker)
            add_btn.show()
            self._layout.addWidget(add_btn)

        r = self.row
        if r >= 0:
            item = self.table.item(r, 1)
            if item is not None:
                item.setText("")
                item.setData(Qt.ItemDataRole.UserRole, ", ".join(self._tags))

        target_w = self.width()
        if target_w <= 50 and self.table is not None:
            target_w = self.sizeHint().width()
        target_h = max(self.sizeHint().height(), 32)
        self._layout.setGeometry(QRect(0, 0, max(target_w, 50), target_h))


class FolderFilterTable(QTableWidget):
    """
    Table widget for displaying and editing folder filters.
    """

    FILTER_TYPES = [
        "OS",
        "Folder",
        "File",
        "NFO",
        "Genre",
        "Actor",
        "Director",
        "Title",
        "Year",
        "META",
        "Last Played",
        "Qty Played",
        "Tag",
    ]

    # Group headers that separate sections in the table and dropdown;
    # displayed as non-selectable separators.
    FILTER_GROUP_HEADERS = {"OS", "NFO", "META"}

    genre_changed = Signal(object)
    root_folder = Signal(object)

    def __init__(
        self,
        genres: list[str],
        media_configs: list[dict],
        tags: list[dict] | None = None,
        tag_store: DbTags | None = None,
        state: object | None = None,
        readonly: bool = False,
    ):
        super().__init__()
        self.genres = genres
        self.media_configs = media_configs
        self.tags = tags
        self._tag_store = tag_store
        self._state = state
        self.readonly = readonly
        self._setup_ui()

    @property
    def tag_store(self) -> DbTags | None:
        return self._tag_store

    @tag_store.setter
    def tag_store(self, value: DbTags | None) -> None:
        self._tag_store = value
        self._refresh_tag_cells()

    def _setup_ui(self) -> None:
        self.verticalHeader().setVisible(False)
        if self.readonly:
            self.setColumnCount(2)
            self.setHorizontalHeaderLabels(["Filter", "Value"])
        else:
            self.setColumnCount(3)
            self.setHorizontalHeaderLabels(["Filter", "Value", ""])
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        self.setStyleSheet(APP_THEME.table_qss())

        header = self.horizontalHeader()
        header.setMinimumSectionSize(105)
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, header.ResizeMode.Stretch)
        if not self.readonly:
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        header.sectionResized.connect(lambda *_: self._update_height())
        header.geometriesChanged.connect(self._update_height)
        self._check_empty_state()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_height()

    def _check_empty_state(self) -> None:
        if self.rowCount() == 0:
            self.insertRow(0)
            placeholder_text = (
                "Select a filter from above dropdown"
                if self.readonly
                else "Add a Filter from above"
            )
            if self.readonly:
                placeholder = QLabel(placeholder_text, self)
                placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                placeholder.setFont(
                    QFont(APP_THEME.font_family, APP_THEME.font_size - 6)
                )
                self.setCellWidget(0, 0, placeholder)
                item = QTableWidgetItem(placeholder_text)
                self.setItem(0, 0, item)
                self.setSpan(0, 0, 1, self.columnCount())
            else:
                placeholder = QTableWidgetItem(placeholder_text)
                placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
                placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(0, 0, placeholder)
                self.setSpan(0, 0, 1, self.columnCount())
        elif self.rowCount() > 1 and self.columnSpan(0, 0) > 1:
            # Remove placeholder if we have more than 1 row and 0,0 is spanned
            self.removeRow(0)
        elif self.rowCount() == 1 and self.columnSpan(0, 0) > 1:
            # This is the placeholder row, do nothing
            pass

        self._update_height()

    def _update_height(self) -> None:
        self.resizeRowsToContents()
        header_height = self.horizontalHeader().height()
        if header_height <= 0 and self.horizontalHeader().isVisible():
            header_height = max(self.horizontalHeader().sizeHint().height(), 24)
        rows_height = 0
        for i in range(self.rowCount()):
            widget = self.cellWidget(i, 1)
            row_h = self.rowHeight(i)
            if isinstance(widget, FilterTagCloudWidget):
                cloud_h = widget.sizeHint().height()
                target_h = max(cloud_h, 32)
                self.setRowHeight(i, target_h)
                row_h = target_h
            rows_height += max(row_h, 32)

        total_height = header_height + rows_height + 6  # +6 for borders
        self.setFixedHeight(total_height)

    def add_filter(self, filter_type: str, filter_value: str = "") -> None:
        if self.rowCount() == 1 and self.columnSpan(0, 0) > 1:
            self.removeRow(0)

        clean_type = filter_type.casefold().strip()
        if clean_type == "tag":
            tag_row = -1
            for r in range(self.rowCount()):
                if self._filter_type_at(r) == "tag":
                    tag_row = r
                    break
            if tag_row != -1:
                widget = self.cellWidget(tag_row, 1)
                if isinstance(widget, FilterTagCloudWidget):
                    if filter_value:
                        if isinstance(filter_value, list):
                            new_tags = filter_value
                        else:
                            new_tags = [
                                t.strip()
                                for t in str(filter_value).split(",")
                                if t.strip()
                            ]
                        for t in new_tags:
                            widget.add_tag(t)
                    elif not self.readonly:
                        widget.open_picker()
                self._update_height()
                return

        row_nbr = self.rowCount()
        self.insertRow(row_nbr)
        self._set_filter_type_cell(row_nbr, filter_type)
        self._set_filter_value_cell(row_nbr, filter_type, filter_value)
        if not self.readonly:
            self._set_remove_button_cell(row_nbr)
        self.resizeColumnToContents(0)
        self._update_height()
        if clean_type == "tag" and not self.readonly and not filter_value:
            widget = self.cellWidget(row_nbr, 1)
            if isinstance(widget, FilterTagCloudWidget):
                widget.open_picker()

    def _set_filter_type_cell(self, row_nbr: int, filter_type: str) -> None:
        clean_type = filter_type.casefold().strip()
        if clean_type in ("os", "nfo", "meta"):
            label_text = filter_type.strip()
        else:
            label_text = f"  {filter_type.strip()}"
        if self.readonly:
            label = QLabel(label_text, self)
            label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
            label.setStyleSheet("padding-left: 4px; padding-right: 4px;")
            self.setCellWidget(row_nbr, 0, label)
            item = QTableWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, label_text)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row_nbr, 0, item)
            self.resizeColumnToContents(0)
            return

        filter_type_label = QTableWidgetItem(label_text)
        if clean_type in ("os", "nfo", "meta"):
            filter_type_label.setFlags(Qt.ItemFlag.NoItemFlags)
        else:
            filter_type_label.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )
        filter_type_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
        self.setItem(row_nbr, 0, filter_type_label)

    def _get_tag_store(self) -> DbTags | None:
        return self._tag_store or (
            getattr(self._state, "tag_store", None) if self._state else None
        )

    def _get_tag_info(self, tag_name: str) -> tuple[str, int]:
        tag_store = self._get_tag_store()
        catalog_tags = (
            tag_store.list_tags()
            if tag_store and hasattr(tag_store, "list_tags")
            else (
                getattr(self._state, "tags", None) if self._state else (self.tags or [])
            )
        ) or []
        tag_colors = {
            t["tag"].casefold(): t.get("color", "#808080")
            for t in catalog_tags
            if isinstance(t, dict) and "tag" in t
        }
        counts = (
            tag_store.get_tag_counts()
            if tag_store and hasattr(tag_store, "get_tag_counts")
            else {}
        ) or {}
        color = tag_colors.get(tag_name.casefold(), "#808080")
        count = counts.get(tag_name.casefold(), 0)
        return color, count

    def _style_tag_button(self, btn: QPushButton, tag_name: str) -> None:
        btn.setProperty("tag_value", tag_name)
        if not tag_name or tag_name == "- Select Tag -":
            btn.setText("- Select Tag -")
            btn.setProperty("preserve_custom_style", False)
            btn.setStyleSheet("")
            APP_THEME.setup_button(btn)
        else:
            color, count = self._get_tag_info(tag_name)
            btn.setText(f"{tag_name} ({count})")
            btn.setProperty("preserve_custom_style", True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ color: {get_contrast_text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 6px; font-weight: bold; border: 0; }}"
            )

    def _refresh_tag_cells(self) -> None:
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 1)
            if isinstance(widget, FilterTagCloudWidget):
                widget.refresh()

    def _set_filter_value_cell(
        self, row_nbr: int, filter_type: str, filter_value: str = ""
    ) -> None:
        clean_type = filter_type.casefold().strip()
        if clean_type == "tag":
            tag_cloud = FilterTagCloudWidget(
                table=self, readonly=self.readonly, parent=self
            )
            if isinstance(filter_value, list):
                tags = [
                    str(t).strip()
                    for t in filter_value
                    if str(t).strip() and str(t).strip() != "- Select Tag -"
                ]
            elif (
                isinstance(filter_value, str)
                and filter_value.strip()
                and filter_value.strip() != "- Select Tag -"
            ):
                tags = [
                    t.strip()
                    for t in filter_value.split(",")
                    if t.strip() and t.strip() != "- Select Tag -"
                ]
            else:
                tags = []
            tag_cloud.set_tags(tags)
            self.setCellWidget(row_nbr, 1, tag_cloud)
            item = QTableWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, ", ".join(tags))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row_nbr, 1, item)
            return

        if self.readonly:
            label = QLabel(filter_value, self)
            label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))
            label.setStyleSheet("padding-left: 4px; padding-right: 4px;")
            self.setCellWidget(row_nbr, 1, label)
            item = QTableWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, filter_value)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row_nbr, 1, item)
            return

        if clean_type == "genre":
            # For Genre, we use a new combo box
            combo = QComboBox(self)
            combo.addItem("-none-")
            for genre in self.genres:
                combo.addItem(genre)
            if filter_value:
                combo.setCurrentText(filter_value)
            APP_THEME.setup_combo_box(combo)
            combo.currentTextChanged.connect(self._on_genre_changed)
            self.setCellWidget(row_nbr, 1, combo)
            return

        if clean_type == "media":
            # For Media, we use a new combo box
            combo = QComboBox(self)
            combo.addItem("- Select Folder -", userData="")
            for config in self.media_configs:
                combo.addItem(config["label"], userData=config["path"])
            if filter_value:
                # Try to find by text first, then by data if that fails
                index = combo.findText(filter_value)
                if index == -1:
                    index = combo.findData(filter_value)
                if index != -1:
                    combo.setCurrentIndex(index)
            combo.currentIndexChanged.connect(
                lambda idx: self._on_root_folder_changed(idx, combo)
            )
            self.setCellWidget(row_nbr, 1, combo)
            return

        if clean_type == "last played":
            widget = FilterLastPlayedWidget(
                table=self, readonly=self.readonly, parent=self
            )
            if filter_value:
                widget.set_value(filter_value)
            self.setCellWidget(row_nbr, 1, widget)
            item = QTableWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, filter_value)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row_nbr, 1, item)
            return

        if clean_type == "qty played":
            widget = FilterQtyPlayedWidget(
                table=self, readonly=self.readonly, parent=self
            )
            if filter_value:
                widget.set_value(filter_value)
            self.setCellWidget(row_nbr, 1, widget)
            item = QTableWidgetItem("")
            item.setData(Qt.ItemDataRole.UserRole, filter_value)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.setItem(row_nbr, 1, item)
            return

        filter_type_value = QTableWidgetItem(filter_value)
        if filter_type.upper() in ("OS", "NFO", "META"):
            filter_type_value.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )
        else:
            filter_type_value.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
            )
        filter_type_value.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 6))

        self.setItem(row_nbr, 1, filter_type_value)

    def _set_remove_button_cell(self, row_nbr: int) -> None:

        remove_btn = QToolButton(self)
        remove_btn.setIcon(APP_THEME.icon("fa6s.trash-can", color=APP_THEME.text_color))
        remove_btn.setToolTip("Delete Criteria")
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
        widget = self.cellWidget(row, 0)
        if isinstance(widget, QLabel):
            return widget.text().casefold().strip()
        filter_item = self.item(row, 0)
        if filter_item is None:
            return ""
        user_data = filter_item.data(Qt.ItemDataRole.UserRole)
        if user_data:
            return str(user_data).casefold().strip()
        return filter_item.text().casefold().strip()

    def _filter_value_at(self, row: int, filter_type: str) -> str:
        widget = self.cellWidget(row, 1)
        if isinstance(widget, FilterTagCloudWidget):
            return ", ".join(widget.get_tags())
        if isinstance(widget, FilterLastPlayedWidget):
            return widget.get_value()
        if isinstance(widget, FilterQtyPlayedWidget):
            return widget.get_value()
        if isinstance(widget, QLabel):
            tag_val = widget.property("tag_value")
            if tag_val is not None:
                return str(tag_val).strip()
            return widget.text().strip()
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

        if isinstance(widget, (QPushButton, QToolButton)):
            tag_val = widget.property("tag_value")
            if tag_val is not None:
                return "" if tag_val == "- Select Tag -" else str(tag_val).strip()
            text = widget.text().strip()
            return "" if text == "- Select Tag -" else text

        value_item = self.item(row, 1)
        if value_item is not None:
            user_data = value_item.data(Qt.ItemDataRole.UserRole)
            if user_data:
                return str(user_data).strip()
            return value_item.text().strip()
        return ""

    def _open_tag_picker(
        self, anchor_widget: QWidget, tag_cloud: FilterTagCloudWidget
    ) -> None:
        from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog

        popup = TagPickerDialog(self.window(), allow_create=False, allow_delete=False)
        tag_store = self._get_tag_store()
        catalog_tags = (
            tag_store.list_tags()
            if tag_store and hasattr(tag_store, "list_tags")
            else (
                getattr(self._state, "tags", None) if self._state else (self.tags or [])
            )
        ) or []
        tag_colors = {
            t["tag"].casefold(): t.get("color", "#808080")
            for t in catalog_tags
            if isinstance(t, dict) and "tag" in t
        }
        counts = (
            tag_store.get_tag_counts()
            if tag_store and hasattr(tag_store, "get_tag_counts")
            else {}
        ) or {}
        current_tags = list(tag_cloud.get_tags())
        popup.set_data(current_tags, tag_colors, catalog_tags, counts)

        def on_tag_selected(tag: str):
            tag_cloud.add_tag(tag)
            popup.close()

        popup.tag_selected.connect(on_tag_selected)
        popup.tag_created.connect(on_tag_selected)
        pos = anchor_widget.mapToGlobal(anchor_widget.rect().bottomLeft())
        screen = self.window().screen() if self.window() else None
        if screen is not None:
            available = screen.availableGeometry()
            popup_w = min(max(520, popup.sizeHint().width()), available.width() - 20)
            popup_h = min(max(420, popup.sizeHint().height()), available.height() - 20)
            popup.resize(popup_w, popup_h)
            x = min(pos.x(), available.right() - popup.width() - 10)
            y = min(pos.y(), available.bottom() - popup.height() - 10)
            popup.move(max(x, available.left()), max(y, available.top()))
        else:
            popup.resize(520, 420)
            popup.move(pos)
        popup.show()

    def apply_theme(self) -> None:
        # Tables need specific styling and font application which is handled by ThemeManager
        APP_THEME.refresh_theme(self)

    def _on_genre_changed(self, genre: str):
        payload = SignalPayload(
            data=genre,
            sender=self.__class__.__name__,
            name="Genre Changed",
            description="Emitted when the genre changes in FolderFilterTable.",
            flow=SignalFlow.USER_INPUT,
        )
        self.genre_changed.emit(payload)

    def _on_root_folder_changed(self, idx: int, combo: QComboBox):
        if idx > 0:
            payload = SignalPayload(
                data=combo.itemData(idx),
                sender=self.__class__.__name__,
                name="Root Folder Changed",
                description="Emitted when a root folder is selected in FolderFilterTable.",
                flow=SignalFlow.USER_INPUT,
            )
            self.root_folder.emit(payload)
