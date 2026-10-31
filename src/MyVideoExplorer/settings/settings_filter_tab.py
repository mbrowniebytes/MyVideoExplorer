from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QModelIndex, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable
from MyVideoExplorer.media_nav_search.filter_criteria_dialog import FilterCriteriaDialog
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.combo_box_delegate import GroupedComboBoxDelegate

if TYPE_CHECKING:
    from MyVideoExplorer.db.db_tags import DbTags


# TODO: centralize w/ folder_filter
GENRES = sorted(
    ["Action", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Drama", "Adventure"]
)


class SettingsFilterTab(SettingsBaseTab):
    """
    Compact filter list tab for Settings -> Filters.

    Shows all saved filters in a single-row-per-filter table with search and
    filter controls. The edit button (or double-click) opens a dialog for
    editing criteria; the delete button removes the filter.
    """

    COL_EDIT = 0
    COL_NAME = 1
    COL_COUNT = 2
    COL_TYPES = 3
    COL_DELETE = 4
    COLUMN_COUNT = 5

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        tag_store: DbTags | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util, parent)
        self.state = state
        self._tag_store: DbTags | None = tag_store

        # Search/filter state
        self._search_text = ""
        self._search_type = ""
        self._search_tags: list[str] = []

        self._filter_table_widget: QTableWidget | None = None
        self._search_edit: QLineEdit | None = None
        self._type_combo: QComboBox | None = None
        self._tag_filter_label: QLabel | None = None
        self._clear_tag_btn: QToolButton | None = None
        self._filtered_filters: list[dict[str, Any]] = []
        # Keeps the non-blocking dialog alive while it is open
        self._active_dialog: FilterCriteriaDialog | None = None
        # Sorting state for the filter list table
        self._sort_column: int = self.COL_NAME
        self._sort_order = Qt.SortOrder.AscendingOrder

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.main_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.main_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(15)

        self._build_ui()
        self.content_layout.addStretch()

        scroll.setWidget(self.main_widget)
        self._layout.addWidget(scroll)

    @property
    def tag_store(self) -> DbTags | None:
        return self._tag_store

    @tag_store.setter
    def tag_store(self, value: DbTags | None) -> None:
        self._tag_store = value

    def _build_ui(self) -> None:
        # Search bar section
        search_group = QGroupBox("Filters", self)
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(8)

        # Search controls row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)

        # Search by name
        search_label = QLabel("Search:", self)
        search_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        controls_row.addWidget(search_label)

        self._search_edit = QLineEdit(self)
        self._search_edit.setPlaceholderText("Filter by name...")
        self._search_edit.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self._search_edit.textChanged.connect(self._on_search_changed)
        controls_row.addWidget(self._search_edit, 1)

        # Filter by criteria type
        type_label = QLabel("Type:", self)
        type_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        controls_row.addWidget(type_label)

        self._type_combo = QComboBox(self)
        self._type_combo.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self._type_combo.addItem("- All Types -", userData="")
        under_group = False
        for ft in FolderFilterTable.FILTER_TYPES:
            if ft in FolderFilterTable.FILTER_GROUP_HEADERS:
                self._type_combo.addItem(ft, userData=ft)
                index = self._type_combo.count() - 1
                model = self._type_combo.model()
                if model is not None and isinstance(model, QStandardItemModel):
                    item = model.item(index)
                    if item is not None:
                        item.setEnabled(False)
                under_group = True
            elif under_group:
                self._type_combo.addItem("    " + ft, userData=ft)
            else:
                self._type_combo.addItem(ft, userData=ft)
        # Apply grouped delegate for extra height on group headers
        self._type_combo.setItemDelegate(
            GroupedComboBoxDelegate(
                FolderFilterTable.FILTER_GROUP_HEADERS, self._type_combo
            )
        )
        self._type_combo.currentIndexChanged.connect(self._on_search_changed)
        self._type_combo.setMinimumWidth(160)
        controls_row.addWidget(self._type_combo)

        # Tag filter button
        tag_btn = QToolButton(self)
        tag_btn.setIcon(APP_THEME.icon("fa6s.tag", color=APP_THEME.text_color))
        tag_btn.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        tag_btn.setToolTip("Filter by tag values")
        tag_btn.clicked.connect(self._on_tag_filter_clicked)
        controls_row.addWidget(tag_btn)

        # Active tag filter (hidden until tags are picked)
        self._tag_filter_label = QLabel(self)
        self._tag_filter_label.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size - 4)
        )
        controls_row.addWidget(self._tag_filter_label)

        self._clear_tag_btn = QToolButton(self)
        self._clear_tag_btn.setIcon(
            APP_THEME.icon("fa6s.xmark", color=APP_THEME.text_color)
        )
        self._clear_tag_btn.setIconSize(QSize(14, 14))
        self._clear_tag_btn.setAutoRaise(True)
        self._clear_tag_btn.setToolTip("Clear tag filter")
        self._clear_tag_btn.clicked.connect(self._clear_tag_filter)
        controls_row.addWidget(self._clear_tag_btn)
        self._update_tag_filter_label()

        # Add filter button, on the same row as the search controls
        add_btn = QToolButton(self)
        add_btn.setIcon(APP_THEME.icon("fa6s.circle-plus", color=APP_THEME.text_color))
        add_btn.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        add_btn.setToolTip("Add New Filter")
        add_btn.clicked.connect(self.open_add_filter)
        controls_row.addWidget(add_btn)

        search_layout.addLayout(controls_row)

        self.content_layout.addWidget(search_group)

        # Main filter list table
        self._filter_table_widget = QTableWidget(self)
        self._filter_table_widget.setColumnCount(self.COLUMN_COUNT)
        self._filter_table_widget.setHorizontalHeaderLabels(
            ["", "Filter Name", "Criteria Count", "Criteria Types", ""]
        )
        self._filter_table_widget.verticalHeader().setVisible(False)
        # One line per filter; long text is elided with "..."
        self._filter_table_widget.setWordWrap(False)
        self._filter_table_widget.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._filter_table_widget.setAlternatingRowColors(True)
        self._filter_table_widget.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._filter_table_widget.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._filter_table_widget.setStyleSheet(APP_THEME.table_qss())

        header = self._filter_table_widget.horizontalHeader()
        header.setMinimumSectionSize(36)
        header.setSectionResizeMode(self.COL_EDIT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            self.COL_COUNT, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_TYPES, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_DELETE, QHeaderView.ResizeMode.Fixed)
        self._filter_table_widget.setColumnWidth(self.COL_EDIT, 36)
        self._filter_table_widget.setColumnWidth(self.COL_DELETE, 36)

        # Enable clickable sorting on Name and Count columns
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self._sort_column, self._sort_order)
        header.sortIndicatorChanged.connect(self._on_sort_changed)

        self._filter_table_widget.doubleClicked.connect(self._on_double_click)
        self.content_layout.addWidget(self._filter_table_widget, 1)

        # Bottom buttons: Save and Reset
        save_btn_container = QWidget(self)
        save_btn_layout = QHBoxLayout(save_btn_container)
        save_btn_layout.setContentsMargins(20, 15, 20, 15)

        self.save_btn = QPushButton("Save Filter Settings", parent=self)
        self.save_btn.setFixedWidth(200)
        self.save_btn.clicked.connect(self._save_filter_settings)

        self.reset_btn = self._build_reset_button(
            "Reset Filter Settings", self.reset_settings
        )
        self.reset_btn.setFixedWidth(190)

        spacer = QWidget(self)
        spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        save_btn_layout.addWidget(self.reset_btn)
        save_btn_layout.addWidget(spacer)
        save_btn_layout.addWidget(self.save_btn)
        self.content_layout.addWidget(
            save_btn_container,
            alignment=Qt.AlignmentFlag.AlignBottom,
        )

        # Populate the filter list
        self._refresh_filter_list()

    def reset_settings(self) -> None:
        """Reset settings for this tab."""
        self.state.load_filters()
        self._refresh_filter_list()
        self.reset_save_button()
        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Filter Settings Reset",
                description="Filter settings were reset to defaults.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("Filters Settings reset")

    def _on_search_changed(self) -> None:
        """Handle search text or type filter change."""
        if self._search_edit is not None:
            self._search_text = self._search_edit.text().strip().lower()
        if self._type_combo is not None:
            self._search_type = str(self._type_combo.currentData() or "")
        self._refresh_filter_list()

    def _on_sort_changed(self, column: int, order: Qt.SortOrder) -> None:
        """Handle column header click to sort the filter list."""
        # Only allow sorting on Name and Count columns
        if column not in (self.COL_NAME, self.COL_COUNT):
            if self._filter_table_widget is not None:
                header = self._filter_table_widget.horizontalHeader()
                header.setSortIndicator(self._sort_column, self._sort_order)
            return
        self._sort_column = column
        self._sort_order = order
        self._refresh_filter_list()

    def _clear_tag_filter(self) -> None:
        self._search_tags = []
        self._update_tag_filter_label()
        self._refresh_filter_list()

    def _update_tag_filter_label(self) -> None:
        """Show the active tag filter, or hide it when no tags are picked."""
        has_tags = bool(self._search_tags)
        if self._tag_filter_label is not None:
            self._tag_filter_label.setText(
                f"Tags: {', '.join(self._search_tags)}" if has_tags else ""
            )
            self._tag_filter_label.setVisible(has_tags)
        if self._clear_tag_btn is not None:
            self._clear_tag_btn.setVisible(has_tags)

    def _on_tag_filter_clicked(self) -> None:
        """Open tag picker dialog to filter the list by tag values."""
        if self._tag_store is None:
            return
        popup = TagPickerDialog(self.window(), allow_create=False, allow_delete=False)
        catalog_tags = self._tag_store.list_tags()
        tag_colors = {
            item["tag"].casefold(): item.get("color", "#808080")
            for item in catalog_tags
            if isinstance(item, dict) and "tag" in item
        }
        counts = self._tag_store.get_tag_counts()
        popup.set_data(list(self._search_tags), tag_colors, catalog_tags, counts)

        def on_tag_selected(tag: str) -> None:
            if tag and tag.casefold() not in {t.casefold() for t in self._search_tags}:
                self._search_tags.append(tag)
            popup.close()
            self._update_tag_filter_label()
            self._refresh_filter_list()

        popup.tag_selected.connect(on_tag_selected)
        popup.tag_created.connect(on_tag_selected)

        pos = self.mapToGlobal(self.rect().bottomLeft())
        screen = self.screen()
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

    def _matches_search(self, filter_cfg: dict[str, Any]) -> bool:
        """Check if a filter matches the current search criteria."""
        name = filter_cfg.get("name", "").lower()
        filters = filter_cfg.get("filters", [])

        # Match by name
        if self._search_text and self._search_text not in name:
            return False

        # Match by criteria type
        if self._search_type:
            types_in_filter = {f.get("filter", "").casefold() for f in filters}
            if self._search_type.casefold() not in types_in_filter:
                return False

        # Match by tag values
        if self._search_tags:
            tag_values_in_filter: set[str] = set()
            for f in filters:
                if f.get("filter", "").casefold() == "tag":
                    val = f.get("value", "")
                    for t in val.split(","):
                        tag_values_in_filter.add(t.strip().casefold())
            search_tag_set = {t.casefold() for t in self._search_tags}
            if not search_tag_set.intersection(tag_values_in_filter):
                return False

        return True

    def _refresh_filter_list(self) -> None:
        """Populate the filter table from state.saved_filters, applying search filters."""
        table = self._filter_table_widget
        if table is None:
            return

        table.setRowCount(0)
        table.clearSpans()

        saved = self.state.saved_filters
        if not saved:
            self._show_placeholder(table, "No saved filters found.")
            return

        # Apply search filter
        filtered = [f for f in saved if self._matches_search(f)]
        if not filtered:
            self._show_placeholder(table, "No filters match the search criteria.")
            return

        # Apply sorting
        if self._sort_column == self.COL_NAME:
            filtered.sort(
                key=lambda f: f.get("name", "").lower(),
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        elif self._sort_column == self.COL_COUNT:
            filtered.sort(
                key=lambda f: len(f.get("filters", [])),
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )

        cell_font = QFont(APP_THEME.font_family, APP_THEME.font_size - 4)
        table.setRowCount(len(filtered))
        for row_idx, filter_cfg in enumerate(filtered):
            name = filter_cfg.get("name", "")
            filters = filter_cfg.get("filters", [])
            criteria_count = len(filters)
            criteria_types = sorted({f.get("filter", "") for f in filters})
            types_str = ", ".join(criteria_types) if criteria_types else "-"

            table.setCellWidget(
                row_idx,
                self.COL_EDIT,
                self._make_row_button(
                    "fa6s.pen-to-square",
                    f"Edit filter '{name}'",
                    partial(self.open_edit_dialog, filter_cfg),
                ),
            )

            # Name cell (elided with "..." when too long)
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(name)
            name_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_NAME, name_item)

            count_item = QTableWidgetItem(str(criteria_count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            count_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_COUNT, count_item)

            types_item = QTableWidgetItem(types_str)
            types_item.setToolTip(types_str)
            types_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_TYPES, types_item)

            table.setCellWidget(
                row_idx,
                self.COL_DELETE,
                self._make_row_button(
                    "fa6s.trash-can",
                    f"Delete filter '{name}'",
                    partial(self._request_delete, name),
                ),
            )

        # Store the filtered list for row lookup
        self._filtered_filters = filtered

    def _make_row_button(self, icon_name: str, tooltip: str, slot: Any) -> QToolButton:
        btn = QToolButton(self._filter_table_widget)
        btn.setIcon(APP_THEME.icon(icon_name, color=APP_THEME.text_color))
        btn.setIconSize(QSize(14, 14))
        btn.setAutoRaise(True)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Ignore the bool argument of clicked
        btn.clicked.connect(lambda _checked=False: slot())
        return btn

    def _show_placeholder(self, table: QTableWidget, text: str) -> None:
        """Show a placeholder message when no filters are present."""
        self._filtered_filters = []
        table.setRowCount(1)
        placeholder = QTableWidgetItem(text)
        placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
        placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
        table.setItem(0, 0, placeholder)
        table.setSpan(0, 0, 1, self.COLUMN_COUNT)

    def _on_double_click(self, index: QModelIndex | None = None) -> None:
        """Handle double-click on a filter row to open the edit dialog."""
        table = self._filter_table_widget
        if table is None:
            return
        row = index.row() if index is not None else table.currentRow()
        if row < 0 or row >= len(self._filtered_filters):
            return
        self.open_edit_dialog(self._filtered_filters[row])

    def open_edit_dialog(self, filter_cfg: dict[str, Any]) -> None:
        original_name = str(filter_cfg.get("name", ""))
        dialog = self._make_dialog(
            filter_name=original_name,
            filters=list(filter_cfg.get("filters", [])),
            edit_mode=True,
        )
        dialog.saved.connect(partial(self._on_dialog_save, original_name))
        dialog.deleted.connect(self._on_dialog_delete)
        self._show_dialog(dialog)

    def open_add_filter(self, filters: list[dict[str, str]] | None = None) -> None:
        """Open dialog to add a new filter, optionally pre-filled with criteria."""
        dialog = self._make_dialog(
            filter_name="", filters=filters or [], edit_mode=False
        )
        dialog.saved.connect(partial(self._on_dialog_save, ""))
        self._show_dialog(dialog)

    def _make_dialog(
        self, filter_name: str, filters: list[dict[str, str]], edit_mode: bool
    ) -> FilterCriteriaDialog:
        return FilterCriteriaDialog(
            genres=GENRES,
            media_configs=self.state.media_configs,
            tags=self.state.tags,
            tag_store=self._tag_store,
            state=self.state,
            filter_name=filter_name,
            filters=filters,
            edit_mode=edit_mode,
            readonly=False,
            parent=self.window(),
        )

    def _show_dialog(self, dialog: FilterCriteriaDialog) -> None:
        """
        Show the dialog non-blocking, positioned near the filter list table.

        A nested ``exec()`` event loop under QtAsyncio, combined with the
        settings_changed refresh chain running inside it, crashed the app on save.
        ``open()`` keeps the dialog modal without a nested loop.
        """
        if self._active_dialog is not None:
            self._active_dialog.close()
        dialog.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        dialog.finished.connect(lambda _result: self._on_dialog_finished(dialog))
        self._active_dialog = dialog

        # Position the dialog near the filter list table so the folder nav is still visible
        table = self._filter_table_widget
        if table is not None:
            dialog.resize(600, 480)
            # Map the table's bottom-right corner to global coordinates
            bottom_right = table.mapToGlobal(table.rect().bottomRight())
            screen = self.screen()
            if screen is not None:
                available = screen.availableGeometry()
                dialog_w = dialog.width()
                dialog_h = dialog.height()
                # Position to the left of the table, aligned with its top
                x = bottom_right.x() - dialog_w - 10
                y = table.mapToGlobal(table.rect().topLeft()).y()
                # Keep within screen bounds
                x = max(x, available.left())
                y = max(y, available.top())
                # If x is still off-screen (dialog wider than available space), align right
                if x + dialog_w > available.right():
                    x = bottom_right.x() + 10
                    x = min(x, available.right() - dialog_w)
                y = min(y, available.bottom() - dialog_h)
                dialog.move(x, y)
        dialog.open()

    def _on_dialog_finished(self, dialog: FilterCriteriaDialog) -> None:
        if self._active_dialog is dialog:
            self._active_dialog = None

    def _on_dialog_save(
        self, original_name: str, name: str, filters: list[dict[str, str]]
    ) -> None:
        """Defer persistence until the dialog has fully closed."""
        QTimer.singleShot(0, partial(self._persist_save, original_name, name, filters))

    def _persist_save(
        self, original_name: str, name: str, filters: list[dict[str, str]]
    ) -> None:
        self.state.save_filter(name, filters, original_name=original_name or None)
        self._refresh_filter_list()

    def _on_dialog_delete(self, name: str) -> None:
        """Defer persistence until the dialog has fully closed."""
        self._request_delete(name)

    def _request_delete(self, name: str) -> None:
        if not name:
            return
        QTimer.singleShot(0, partial(self._persist_delete, name))

    def _persist_delete(self, name: str) -> None:
        self.state.delete_filter(name)
        self._refresh_filter_list()

    def apply_theme(self) -> None:
        super().apply_theme()
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)
        self.setFont(font)
        self._refresh_filter_list()

    def _save_filter_settings(self) -> None:
        """Save only Filters tab settings."""
        self.state.save_filters()
        self.reset_save_button()
        self.saved.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Filter Settings Saved",
                description="Filter settings were saved.",
                flow=SignalFlow.USER_INPUT,
            )
        )
        print("Filters Settings saved")
