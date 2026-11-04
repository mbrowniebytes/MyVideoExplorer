from __future__ import annotations

import logging
from datetime import UTC
from functools import partial
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QModelIndex, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QStandardItemModel
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.db_filters import DbFilters
from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable
from MyVideoExplorer.media_nav_search.filter_criteria_dialog import FilterCriteriaDialog
from MyVideoExplorer.settings.filter_refresh_worker import FilterRefreshWorker
from MyVideoExplorer.settings.filter_scan_worker import FilterScanWorker
from MyVideoExplorer.settings.settings_base_tab import SettingsBaseTab
from MyVideoExplorer.settings.settings_filter_groups_dialog import (
    SettingsFilterGroupsDialog,
)
from MyVideoExplorer.settings.settings_filter_header import SettingsFilterHeader
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog
from MyVideoExplorer.tag_cloud.tag_util import get_contrast_text_color
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton
from MyVideoExplorer.widgets.combo_box_delegate import GroupedComboBoxDelegate
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox

if TYPE_CHECKING:
    from MyVideoExplorer.db.db_tags import DbTags


# TODO: centralize w/ folder_filter
GENRES = sorted(
    ["Action", "Comedy", "Sci-Fi", "Mystery", "Thriller", "Drama", "Adventure"]
)
logger = logging.getLogger(__name__)


class SettingsFilterTab(SettingsBaseTab):
    """
    Compact filter list tab for Settings -> Filters.

    Shows all saved filters in a single-row-per-filter table with search and
    filter controls. The edit button (or double-click) opens a dialog for
    editing criteria; the delete button removes the filter.
    """

    log_util: LogUtil

    COL_EDIT = 0
    COL_NAME = 1
    COL_GROUP = 2
    COL_COUNT = 3
    COL_REFRESH = 4
    COL_CRITERIA_COUNT = 5
    COL_TYPES = 6
    COL_DELETE = 7
    COLUMN_COUNT = 8

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        tag_store: DbTags | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(log_util, parent)
        self.log_util = log_util
        self.state = state
        self._tag_store: DbTags | None = tag_store
        self.state.filter_counts_changed.connect(self._refresh_filter_list)
        self.state.media_folder_selection_changed.connect(
            self._on_media_folder_selection_changed
        )

        # Search/filter state
        self._search_text = ""
        self._search_type = ""
        self._search_tags: list[str] = []
        self._search_group: int | str | None = None

        self._filter_table_widget: QTableWidget | None = None
        self._search_edit: QLineEdit | None = None
        self._criteria_combo: SelectComboBox | None = None
        self._group_combo: SelectComboBox | None = None
        self._tag_btn: QToolButton | None = None
        self._tag_filter_widget: QWidget | None = None
        self._tag_filter_layout: QHBoxLayout | None = None
        self._clear_tag_btn: QToolButton | None = None
        self._refresh_all_btn: QToolButton | None = None
        self._bulk_progress_bar: QProgressBar | None = None
        self._active_refresh_worker: FilterRefreshWorker | None = None
        self._scan_workers: set[FilterScanWorker] = set()
        self._worker_is_bulk = False
        self._progress_index = 0
        self._busy_filter_name: str | None = None
        self._refresh_errors: list[str] = []
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

        # --- Row 1: Search field ---
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        search_label = QLabel("Search:", self)
        search_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        search_row.addWidget(search_label)

        self._search_edit = QLineEdit(self)
        self._search_edit.setPlaceholderText("Filter by name...")
        self._search_edit.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self._search_edit.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_edit, 1)

        self._refresh_all_btn = ActionButton(
            self,
            text="Refresh Filters",
            icon_name="fa6s.arrows-rotate",
            tooltip="Refresh all saved filters",
        )
        self._refresh_all_btn.clicked.connect(self._refresh_all_filters)

        refresh_controls = QWidget(self)
        refresh_layout = QGridLayout(refresh_controls)
        refresh_layout.setContentsMargins(0, 0, 0, 0)
        refresh_layout.setSpacing(0)
        refresh_layout.addWidget(self._refresh_all_btn, 0, 0)
        self._bulk_progress_bar = QProgressBar(self)
        self._bulk_progress_bar.setTextVisible(False)
        self._bulk_progress_bar.setStyleSheet(
            f"QProgressBar {{ background: transparent; border: none; }}"
            f"QProgressBar::chunk {{ background: {APP_THEME.border_color}; }}"
        )
        self._bulk_progress_bar.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._bulk_progress_bar.hide()
        refresh_layout.addWidget(
            self._bulk_progress_bar,
            0,
            0,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
        )
        search_row.addWidget(refresh_controls)

        # Add filter button
        add_btn = ActionButton(
            self, icon_name="fa6s.circle-plus", tooltip="Add New Filter"
        )
        add_btn.clicked.connect(self.open_add_filter)
        search_row.addWidget(add_btn)

        # Filter Groups management button
        groups_btn = ActionButton(
            self, icon_name="fa6s.folder-tree", tooltip="Manage Filter Groups"
        )
        groups_btn.clicked.connect(self.open_groups_dialog)
        search_row.addWidget(groups_btn)

        search_layout.addLayout(search_row)

        # --- Row 2: Filter controls ---
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        # Filter by criteria type
        criteria_label = QLabel("Criteria:", self)
        criteria_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        filter_row.addWidget(criteria_label)

        self._criteria_combo = SelectComboBox(self)
        self._criteria_combo.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self._criteria_combo.addItem("- Any Criteria -", userData="")
        under_group = False
        for ft in FolderFilterTable.FILTER_TYPES:
            if ft in FolderFilterTable.FILTER_GROUP_HEADERS:
                self._criteria_combo.addItem(ft, userData=ft)
                index = self._criteria_combo.count() - 1
                model = self._criteria_combo.model()
                if model is not None and isinstance(model, QStandardItemModel):
                    item = model.item(index)
                    if item is not None:
                        item.setEnabled(False)
                under_group = True
            elif under_group:
                self._criteria_combo.addItem("    " + ft, userData=ft)
            else:
                self._criteria_combo.addItem(ft, userData=ft)
        # Apply grouped delegate for extra height on group headers
        self._criteria_combo.setItemDelegate(
            GroupedComboBoxDelegate(
                FolderFilterTable.FILTER_GROUP_HEADERS, self._criteria_combo
            )
        )
        self._criteria_combo.currentIndexChanged.connect(self._on_search_changed)
        self._criteria_combo.setMinimumWidth(160)
        filter_row.addWidget(self._criteria_combo)

        # Group filter combobox
        group_label = QLabel("Group:", self)
        group_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        filter_row.addWidget(group_label)

        self._group_combo = SelectComboBox(self)
        self._group_combo.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self._group_combo.addItem("- All Groups -", userData="")
        self._group_combo.addItem("Edited Recently", userData="__edited_recently__")
        self._populate_group_filter()
        self._group_combo.currentIndexChanged.connect(self._on_search_changed)
        self._group_combo.setMinimumWidth(140)
        filter_row.addWidget(self._group_combo)

        # Tag filter button
        self._tag_btn = ActionButton(
            self, icon_name="fa6s.tag", tooltip="Filter by tag values"
        )
        self._tag_btn.clicked.connect(self._on_tag_filter_clicked)
        filter_row.addWidget(self._tag_btn)

        # Active tag filter display area (widget with layout for tag chips)
        self._tag_filter_widget = QWidget(self)
        self._tag_filter_layout = QHBoxLayout(self._tag_filter_widget)
        self._tag_filter_layout.setContentsMargins(0, 0, 0, 0)
        self._tag_filter_layout.setSpacing(4)
        filter_row.addWidget(self._tag_filter_widget, 1)

        self._clear_tag_btn = ActionButton(
            self,
            icon_name="fa6s.xmark",
            tooltip="Clear tag filter",
            icon_size=14,
        )
        self._clear_tag_btn.clicked.connect(self._clear_tag_filter)
        filter_row.addWidget(self._clear_tag_btn)
        self._update_tag_filter_label()

        search_layout.addLayout(filter_row)

        self.content_layout.addWidget(search_group)

        # Main filter list table
        self._filter_table_widget = QTableWidget(self)
        self._filter_table_widget.setHorizontalHeader(SettingsFilterHeader(self))
        self._filter_table_widget.setColumnCount(self.COLUMN_COUNT)
        self._filter_table_widget.setHorizontalHeaderLabels(
            [
                "",
                "Filter Name",
                "Group",
                "Media",
                "",
                "Criteria",
                "",
                "",
            ]
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
        header.setSectionsClickable(True)
        header.setMinimumSectionSize(36)
        header.setSectionResizeMode(self.COL_EDIT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            self.COL_GROUP, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_COUNT, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_REFRESH, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(
            self.COL_CRITERIA_COUNT, QHeaderView.ResizeMode.Fixed
        )
        header.setSectionResizeMode(self.COL_TYPES, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_DELETE, QHeaderView.ResizeMode.Fixed)
        self._filter_table_widget.setColumnWidth(self.COL_EDIT, 36)
        self._filter_table_widget.setColumnWidth(self.COL_COUNT, 50)
        self._filter_table_widget.setColumnWidth(self.COL_REFRESH, 32)
        self._filter_table_widget.setColumnWidth(self.COL_CRITERIA_COUNT, 40)
        self._filter_table_widget.setColumnWidth(self.COL_DELETE, 36)

        # Enable clickable sorting on name, group, and count columns
        header.setSortIndicatorShown(True)
        header.setSortIndicator(self._sort_column, self._sort_order)
        header.sortIndicatorChanged.connect(self._on_sort_changed)
        if isinstance(header, SettingsFilterHeader):
            header.groupedSortRequested.connect(self._on_sort_changed)

        self._filter_table_widget.doubleClicked.connect(self._on_double_click)
        self.content_layout.addWidget(self._filter_table_widget, 1)

        # Populate the filter list
        self._refresh_filter_list()

    def _on_search_changed(self) -> None:
        """Handle search text or type filter change."""
        if self._search_edit is not None:
            self._search_text = self._search_edit.text().strip().lower()
        if self._criteria_combo is not None:
            self._search_type = str(self._criteria_combo.currentData() or "")
        if self._group_combo is not None:
            group_data = self._group_combo.currentData()
            if group_data == "" or group_data is None:
                self._search_group = None
            elif group_data == "__edited_recently__":
                self._search_group = "__edited_recently__"
            else:
                self._search_group = int(group_data)
        self._refresh_filter_list()

    def _populate_group_filter(self) -> None:
        """Populate the Group filter combobox with available groups."""
        combo = self._group_combo
        if combo is None:
            return
        combo.blockSignals(True)
        # Keep the first two items: "- All Groups -" and "Edited Recently"
        while combo.count() > 2:
            combo.removeItem(2)
        try:
            groups = self.state.list_filter_groups()
            for grp in groups:
                # Exclude "Edited Recently" — already added as special item
                if grp.get("name") == "Edited Recently":
                    continue
                combo.addItem(grp["name"], userData=grp["group_id"])
        except Exception:
            pass
        combo.blockSignals(False)

    def _on_sort_changed(self, column: int, order: Qt.SortOrder) -> None:
        """Handle column header click to sort the filter list."""
        # Allow sorting on name, group, and count columns
        if column not in (
            self.COL_NAME,
            self.COL_GROUP,
            self.COL_COUNT,
            self.COL_CRITERIA_COUNT,
        ):
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
        """Rebuild the tag chips display and show/hide the clear button."""
        self._build_tag_chips()
        has_tags = bool(self._search_tags)
        if self._clear_tag_btn is not None:
            self._clear_tag_btn.setVisible(has_tags)

    def _tag_color(self, tag: str) -> str:
        """Look up the stored color for a tag, falling back to a default."""
        if self._tag_store is not None:
            catalog = self._tag_store.list_tags()
            for item in catalog:
                if (
                    isinstance(item, dict)
                    and item.get("tag", "").casefold() == tag.casefold()
                ):
                    c = item.get("color")
                    if c:
                        return c
        return "#6c8cbf"

    def _build_tag_chips(self) -> None:
        """Rebuild the tag chips widgets from the current search tags."""
        if self._tag_filter_layout is None:
            return
        # Clear existing widgets
        while self._tag_filter_layout.count():
            item = self._tag_filter_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        for tag in self._search_tags:
            chip = self._make_tag_chip(tag)
            self._tag_filter_layout.addWidget(chip)

    def _make_tag_chip(self, tag: str) -> QWidget:
        """Create a styled chip widget for a single tag with a remove button."""
        color = self._tag_color(tag)
        text_color = get_contrast_text_color(color)

        chip = QWidget(self)
        layout = QHBoxLayout(chip)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)

        label = QToolButton(chip)
        label.setText(tag)
        label.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
        label.setStyleSheet(
            f"QToolButton {{ color: {text_color}; "
            f"background-color: {color}; border: 0; border-radius: 5px; padding: 2px 4px; }}"
        )
        layout.addWidget(label)

        remove_btn = QToolButton(chip)
        remove_btn.setText("×")
        remove_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        remove_btn.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(
            f"QToolButton {{ color: {text_color}; background: transparent; "
            f"border: none; font-weight: bold; padding: 0 2px; }}"
        )
        remove_btn.clicked.connect(lambda checked=False, t=tag: self._remove_tag(t))
        layout.addWidget(remove_btn)

        return chip

    def _remove_tag(self, tag: str) -> None:
        """Remove a single tag from the filter and refresh the list."""
        self._search_tags = [
            t for t in self._search_tags if t.casefold() != tag.casefold()
        ]
        self._update_tag_filter_label()
        self._refresh_filter_list()

    def _on_tag_filter_clicked(self) -> None:
        """Open tag picker dialog to filter the list by tag values."""
        if self._tag_store is None:
            return
        if self._tag_btn is None:
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

        # Position the dialog below the tag button, right edge aligned
        anchor = self._tag_btn
        pos = anchor.mapToGlobal(anchor.rect().bottomRight())
        screen = anchor.screen()
        if screen is not None:
            available = screen.availableGeometry()
            popup_w = min(max(520, popup.sizeHint().width()), available.width() - 20)
            popup_h = min(max(420, popup.sizeHint().height()), available.height() - 20)
            popup.resize(popup_w, popup_h)
            # Align right edge of popup near right edge of the tag button
            x = pos.x() - popup.width()
            y = pos.y() + 10
            # Keep within screen bounds
            x = max(x, available.left())
            x = min(x, available.right() - popup.width() - 10)
            y = max(y, available.top())
            y = min(y, available.bottom() - popup.height() - 10)
            popup.move(x, y)
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

        # Match by group
        if self._search_group is not None:
            filter_group_id = filter_cfg.get("group_id")
            if self._search_group == "__edited_recently__":
                # Check if filter was modified in the last 7 days
                last_modified = filter_cfg.get("last_modified")
                if last_modified is None:
                    return False
                from datetime import datetime, timedelta

                cutoff = datetime.now(UTC) - timedelta(days=7)
                # last_modified might be a datetime or string
                if isinstance(last_modified, str):
                    try:
                        last_modified = datetime.fromisoformat(last_modified)
                    except ValueError, AttributeError:
                        return False
                if last_modified.tzinfo is None:
                    last_modified = last_modified.replace(tzinfo=UTC)
                if last_modified < cutoff:
                    return False
            else:
                if filter_group_id != self._search_group:
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
        elif self._sort_column == self.COL_GROUP:
            filtered.sort(
                key=lambda f: (f.get("group_name") or "(None)").lower(),
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        elif self._sort_column == self.COL_COUNT:
            filtered.sort(
                key=lambda f: self._sort_count_key(f),
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        elif self._sort_column == self.COL_CRITERIA_COUNT:
            filtered.sort(
                key=self._criteria_count_key,
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
            is_system = filter_cfg.get("is_system", False)

            table.setCellWidget(
                row_idx,
                self.COL_EDIT,
                self._make_row_button(
                    "fa6s.pen-to-square",
                    f"Edit filter '{name}'",
                    partial(self.open_edit_dialog, filter_cfg),
                ),
            )

            match_count = self._display_count(filter_cfg)
            count_item = QTableWidgetItem(
                str(match_count) if match_count is not None else "-"
            )
            count_item.setData(
                Qt.ItemDataRole.UserRole,
                int(match_count) if match_count is not None else -1,
            )
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            count_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_COUNT, count_item)

            refresh_button = self._make_row_button(
                "fa6s.arrows-rotate",
                f"Refresh filter '{name}'",
                partial(self._refresh_one_filter, name),
            )
            if self._active_refresh_worker is not None:
                refresh_button.setEnabled(False)
                if self._busy_filter_name == name:
                    refresh_button.setIcon(
                        APP_THEME.icon("fa6s.spinner", color=APP_THEME.text_color)
                    )
                    refresh_button.setToolTip(f"Refreshing filter '{name}'")
            table.setCellWidget(row_idx, self.COL_REFRESH, refresh_button)

            # Name cell (elided with "..." when too long)
            name_item = QTableWidgetItem(name)
            name_item.setToolTip(name)
            if is_system:
                name_item.setIcon(
                    APP_THEME.icon("fa6s.lock", color=APP_THEME.config.color_text_muted)
                )
                name_item.setToolTip(f"{name}\n(System filter)")
            elif filter_cfg.get("sort_option") == "manual" and filter_cfg.get(
                "needs_rebuild"
            ):
                name_item.setIcon(
                    APP_THEME.icon(
                        "fa6s.triangle-exclamation",
                        color=APP_THEME.config.color_text_muted,
                    )
                )
                name_item.setToolTip(
                    f"{name}\nManual list needs refresh to rebuild stale entries."
                )
            name_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_NAME, name_item)

            # Group column
            group_name = filter_cfg.get("group_name") or "(None)"
            group_item = QTableWidgetItem(str(group_name))
            group_item.setToolTip(str(group_name))
            group_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_GROUP, group_item)

            criteria_count_item = QTableWidgetItem(str(criteria_count))
            criteria_count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            criteria_count_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_CRITERIA_COUNT, criteria_count_item)

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

    def validate_manual_items_after_scan(self, media_config: dict[str, Any]) -> None:
        store = self._filter_store()
        media_folder = str(media_config.get("path", "")).strip()
        if store is None or not media_folder:
            return
        worker = FilterScanWorker(store, media_folder)
        worker.setParent(self)
        self._scan_workers.add(worker)
        worker.updated.connect(self._on_scan_filter_validation_updated)
        worker.failed.connect(self._on_scan_filter_validation_failed)
        worker.finished.connect(lambda: self._finish_scan_worker(worker))
        worker.start()

    def _on_scan_filter_validation_updated(self, names: list[str]) -> None:
        if not names:
            return
        self.state.load_filters()
        self._refresh_filter_list()

    def _on_scan_filter_validation_failed(self, error: str) -> None:
        logger.error("Manual-filter scan validation failed: %s", error)
        QMessageBox.warning(
            self,
            "Manual Filter Scan Check Failed",
            f"Manual filter entries could not be checked after the scan:\n{error}",
        )

    def _finish_scan_worker(self, worker: FilterScanWorker) -> None:
        self._scan_workers.discard(worker)
        worker.deleteLater()

    def _make_row_button(self, icon_name: str, tooltip: str, slot: Any) -> QToolButton:
        if icon_name == "fa6s.trash-can":
            btn = DelayedDeleteButton(self._filter_table_widget, icon_name=icon_name)
        else:
            btn = ActionButton(self._filter_table_widget, icon_name=icon_name)
        btn.setIconSize(QSize(14, 14))
        btn.setToolTip(tooltip)
        # Ignore the bool argument of clicked
        btn.clicked.connect(lambda _checked=False: slot())
        return btn

    def _filter_store(self) -> DbFilters | None:
        store = getattr(self.state, "filter_store", None)
        return store if isinstance(store, DbFilters) else None

    def _display_count(self, filter_cfg: dict[str, Any]) -> int | None:
        store = self._filter_store()
        if store is None:
            count = filter_cfg.get("total_count")
            return int(count) if count is not None else None
        return store.get_display_count(
            str(filter_cfg.get("name", "")),
            getattr(self.state, "selected_media_folders", []),
        )

    def _sort_count_key(self, filter_cfg: dict[str, Any]) -> tuple[bool, int]:
        count = self._display_count(filter_cfg)
        return count is not None, count or 0

    @staticmethod
    def _criteria_count_key(filter_cfg: dict[str, Any]) -> int:
        return len(filter_cfg.get("filters", []))

    def _on_media_folder_selection_changed(self, _folders: object = None) -> None:
        self._refresh_filter_list()

    def _ordered_saved_filters(self) -> list[dict[str, Any]]:
        filters = list(self.state.saved_filters)
        if self._sort_column == self.COL_NAME:
            filters.sort(
                key=lambda item: str(item.get("name", "")).casefold(),
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        elif self._sort_column == self.COL_GROUP:
            filters.sort(
                key=lambda item: (item.get("group_name") or "(None)").casefold(),
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        elif self._sort_column == self.COL_COUNT:
            filters.sort(
                key=self._sort_count_key,
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        elif self._sort_column == self.COL_CRITERIA_COUNT:
            filters.sort(
                key=self._criteria_count_key,
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        return filters

    def _refresh_one_filter(self, name: str) -> None:
        self._start_filter_refresh([name], is_bulk=False)

    def _refresh_all_filters(self) -> None:
        self._start_filter_refresh(
            [str(item.get("name", "")) for item in self._ordered_saved_filters()],
            is_bulk=True,
        )

    def _start_filter_refresh(self, names: list[str], is_bulk: bool) -> None:
        store = self._filter_store()
        names = [name for name in names if name]
        if store is None or not names or self._active_refresh_worker is not None:
            return

        self._worker_is_bulk = is_bulk
        self._progress_index = 0
        self._busy_filter_name = None
        self._refresh_errors = []
        if self._refresh_all_btn is not None:
            self._refresh_all_btn.setEnabled(False)
            if is_bulk:
                self._refresh_all_btn.setIcon(
                    APP_THEME.icon("fa6s.spinner", color=APP_THEME.text_color)
                )
                self._refresh_all_btn.setToolTip("Refreshing saved filters")
        table = self._filter_table_widget
        if table is not None:
            for row in range(table.rowCount()):
                button = table.cellWidget(row, self.COL_REFRESH)
                if isinstance(button, QToolButton):
                    button.setEnabled(False)
        if is_bulk:
            if self._bulk_progress_bar is not None:
                self._bulk_progress_bar.setRange(0, len(names))
                self._bulk_progress_bar.setValue(0)
                self._bulk_progress_bar.show()
        worker = FilterRefreshWorker(store, names)
        self._active_refresh_worker = worker
        worker.progress.connect(self._on_filter_refresh_progress)
        worker.updated.connect(self._on_filter_refreshed)
        worker.failed.connect(self._on_filter_refresh_failed)
        worker.finished.connect(self._on_filter_refresh_finished)
        worker.start()

    def _on_filter_refresh_progress(self, index: int, total: int, name: str) -> None:
        if self._busy_filter_name:
            self._set_refresh_button_busy(self._busy_filter_name, False)
        self._busy_filter_name = name
        self._progress_index = index
        if self._worker_is_bulk:
            if self._bulk_progress_bar is not None:
                self._bulk_progress_bar.setValue(index - 1)
            table = self._filter_table_widget
            if table is not None:
                for row, item in enumerate(self._filtered_filters):
                    if item.get("name") == name:
                        name_cell = table.item(row, self.COL_NAME)
                        if name_cell is not None:
                            table.scrollToItem(
                                name_cell, QTableWidget.ScrollHint.PositionAtCenter
                            )
                        break
        self._set_refresh_button_busy(name, True)

    def _on_filter_refreshed(self, name: str) -> None:
        self.state.load_filters()
        self.state.filter_counts_changed.emit()
        self._update_count_row(name)

    def _on_filter_refresh_failed(self, name: str, error: str) -> None:
        self._refresh_errors.append(f"{name}: {error}")

    def _update_count_row(self, name: str) -> None:
        latest = next(
            (item for item in self.state.saved_filters if item.get("name") == name),
            None,
        )
        if latest is None:
            return
        table = self._filter_table_widget
        for row, item in enumerate(self._filtered_filters):
            if item.get("name") != name:
                continue
            self._filtered_filters[row] = latest
            count = self._display_count(latest)
            count_item = table.item(row, self.COL_COUNT) if table is not None else None
            if count_item is not None:
                count_item.setText(str(count) if count is not None else "-")
                count_item.setData(
                    Qt.ItemDataRole.UserRole, int(count) if count is not None else -1
                )
            break

    def _set_refresh_button_busy(self, name: str, busy: bool) -> None:
        table = self._filter_table_widget
        if table is None:
            return
        for row, item in enumerate(self._filtered_filters):
            if item.get("name") != name:
                continue
            button = table.cellWidget(row, self.COL_REFRESH)
            if isinstance(button, QToolButton):
                icon = "fa6s.spinner" if busy else "fa6s.arrows-rotate"
                button.setIcon(APP_THEME.icon(icon, color=APP_THEME.text_color))
                button.setEnabled(not busy and self._active_refresh_worker is None)
                button.setToolTip(
                    f"Refreshing filter '{name}'"
                    if busy
                    else f"Refresh filter '{name}'"
                )
            break

    def _on_filter_refresh_finished(self) -> None:
        worker = self._active_refresh_worker
        self._active_refresh_worker = None
        if worker is not None:
            worker.deleteLater()

        if self._worker_is_bulk:
            if self._bulk_progress_bar is not None:
                self._bulk_progress_bar.setValue(self._bulk_progress_bar.maximum())
                self._bulk_progress_bar.hide()
            if self._refresh_all_btn is not None:
                self._refresh_all_btn.setEnabled(True)
        if self._refresh_all_btn is not None:
            self._refresh_all_btn.setIcon(
                APP_THEME.icon("fa6s.arrows-rotate", color=APP_THEME.text_color)
            )
            self._refresh_all_btn.setToolTip("Refresh all saved filters")
            self._refresh_all_btn.setEnabled(True)
        table = self._filter_table_widget
        if table is not None:
            for row in range(table.rowCount()):
                button = table.cellWidget(row, self.COL_REFRESH)
                if isinstance(button, QToolButton):
                    button.setEnabled(True)
        for item in self._filtered_filters:
            self._set_refresh_button_busy(str(item.get("name", "")), False)
        self._refresh_filter_list()

        if self._refresh_errors:
            QMessageBox.warning(
                self,
                "Filter Refresh Failed",
                "Some saved filters could not be refreshed:\n"
                + "\n".join(self._refresh_errors),
            )

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
        store = self._filter_store()
        is_system = filter_cfg.get("is_system", False)
        # System filters open in readonly mode
        dialog = self._make_dialog(
            filter_name=original_name,
            filters=list(filter_cfg.get("filters", [])),
            sort_option=str(filter_cfg.get("sort_option", "default")),
            manual_items=(
                store.get_manual_items(original_name) if store is not None else []
            ),
            edit_mode=True,
            group_id=filter_cfg.get("group_id"),
            is_system=is_system,
            is_visible=filter_cfg.get("is_visible", True),
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

    def open_groups_dialog(self) -> None:
        """Open the Filter Groups management dialog."""
        popup = SettingsFilterGroupsDialog(
            self.state, self.log_util, parent=self.window()
        )
        popup.open()

    def _make_dialog(
        self,
        filter_name: str,
        filters: list[dict[str, str]],
        edit_mode: bool,
        sort_option: str = "default",
        manual_items: list[dict[str, Any]] | None = None,
        group_id: int | None = None,
        is_system: bool = False,
        is_visible: bool = True,
    ) -> FilterCriteriaDialog:
        return FilterCriteriaDialog(
            genres=GENRES,
            media_configs=self.state.media_configs,
            tags=self.state.tags,
            tag_store=self._tag_store,
            state=self.state,
            filter_name=filter_name,
            filters=filters,
            sort_option=sort_option,
            manual_items=manual_items,
            edit_mode=edit_mode,
            readonly=False,
            group_id=group_id,
            is_system=is_system,
            is_visible=is_visible,
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

        # Keep the enlarged editor inside the application window.
        table = self._filter_table_widget
        if table is not None:
            parent_window = self.window()
            parent_geometry = parent_window.frameGeometry()
            screen = self.screen()
            if screen is not None:
                available = screen.availableGeometry()
                max_width = min(
                    850, parent_geometry.width() - 20, available.width() - 20
                )
                max_height = min(
                    700, parent_geometry.height() - 20, available.height() - 20
                )
                dialog.setMinimumSize(min(600, max_width), min(500, max_height))
                dialog.resize(max_width, max_height)
                table_top = table.mapToGlobal(table.rect().topLeft())
                candidate_x = (
                    table.mapToGlobal(table.rect().bottomRight()).x()
                    - dialog.width()
                    - 10
                )
                x = max(
                    parent_geometry.left() + 10,
                    min(candidate_x, parent_geometry.right() - dialog.width() - 10),
                )
                y = max(
                    parent_geometry.top() + 10,
                    min(table_top.y(), parent_geometry.bottom() - dialog.height() - 10),
                )
                dialog.move(x, y)
        dialog.open()

    def _on_dialog_finished(self, dialog: FilterCriteriaDialog) -> None:
        if self._active_dialog is dialog:
            self._active_dialog = None

    def _on_dialog_save(
        self,
        original_name: str,
        name: str,
        filters: list[dict[str, str]],
        sort_option: str,
        manual_items: list[dict[str, Any]],
        group_id: int | None = None,
        is_visible: bool = True,
    ) -> None:
        """Defer persistence until the dialog has fully closed."""
        QTimer.singleShot(
            0,
            partial(
                self._persist_save,
                original_name,
                name,
                filters,
                sort_option,
                manual_items,
                group_id,
                is_visible,
            ),
        )

    def _persist_save(
        self,
        original_name: str,
        name: str,
        filters: list[dict[str, str]],
        sort_option: str,
        manual_items: list[dict[str, Any]],
        group_id: int | None = None,
        is_visible: bool = True,
    ) -> None:
        self.state.save_filter(
            name,
            filters,
            original_name=original_name or None,
            sort_option=sort_option,
            manual_items=manual_items if sort_option == "manual" else None,
            group_id=group_id,
            is_visible=is_visible,
        )
        self._refresh_filter_list()
        self._refresh_one_filter(name)

    def _on_dialog_delete(self, name: str) -> None:
        """Defer persistence until the dialog has fully closed."""
        self._request_delete(name)

    def _request_delete(self, name: str) -> None:
        if not name:
            return
        filter_cfg = next(
            (item for item in self.state.saved_filters if item.get("name") == name),
            None,
        )
        count = self._display_count(filter_cfg) if filter_cfg else None
        if count is not None and int(count) > 10:
            answer = QMessageBox.question(
                self,
                "Delete Filter",
                f"'{name}' matches {count} movies. Delete this filter?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
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
