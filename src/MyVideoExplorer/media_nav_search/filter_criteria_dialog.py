from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QModelIndex, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable
from MyVideoExplorer.tag_cloud.tag_util import validate_name
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton
from MyVideoExplorer.widgets.combo_box_delegate import GroupedComboBoxDelegate
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox
from MyVideoExplorer.widgets.name_widget import NameWidget

if TYPE_CHECKING:
    from MyVideoExplorer.db.db_tags import DbTags


class FilterCriteriaDialog(QDialog):
    """
    Modal dialog for viewing and editing filter criteria.

    Supports edit mode (pre-filled with save/cancel/delete) and add mode
    (empty with save/cancel only). System filters keep their criteria fixed while
    allowing visibility and sort settings to be changed. Manual sort mode exposes
    the matched videos with ordering controls. Readonly mode is for display-only use.
    """

    # Emitted when the user saves the filter
    saved = Signal(
        str, list, str, list, int, bool
    )  # name, criteria, sort option, manual order, group_id, is_visible
    # Emitted when the user deletes the filter
    deleted = Signal(str)  # filter_name
    # Emitted when the user clicks Edit in readonly mode
    edit_requested = Signal(str)  # filter_name

    def __init__(
        self,
        genres: list[str],
        media_configs: list[dict],
        tags: list[dict] | None = None,
        tag_store: DbTags | None = None,
        state: object | None = None,
        filter_name: str = "",
        filters: list[dict[str, str]] | None = None,
        sort_option: str = "default",
        manual_items: list[dict[str, Any]] | None = None,
        edit_mode: bool = True,
        readonly: bool = False,
        group_id: int | None = None,
        is_system: bool = False,
        is_visible: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the filter criteria dialog.

        Args:
            genres: List of genre strings for the Genre filter dropdown.
            media_configs: List of media config dicts for the META filter dropdown.
            tags: List of tag dicts for Tag filter display.
            tag_store: Optional DbTags instance for live tag data.
            state: Optional SettingsState for tag access.
            filter_name: Initial filter name (pre-filled in edit mode).
            filters: Initial filter criteria list (pre-filled in edit mode).
            edit_mode: If True, show delete button and pre-fill data.
                      If False, empty form for adding a new filter.
            readonly: If True, disable editing (display-only mode).
            parent: Parent widget.
        """
        super().__init__(parent)
        self.genres = genres
        self.media_configs = media_configs
        self.tags = tags
        self._tag_store = tag_store
        self._state = state
        self._filter_name = filter_name
        self._initial_filters = filters or []
        self._sort_option = sort_option
        self._initial_manual_items = manual_items or []
        self._edit_mode = edit_mode
        self._readonly = readonly
        self._group_id = group_id
        self._is_system = is_system
        self._is_visible = is_visible

        self._name_edit: QLineEdit | None = None
        self._filter_table: FolderFilterTable | None = None
        self._criteria_type_combo: QComboBox | None = None
        self._sort_combo: SelectComboBox | None = None
        self._group_combo: SelectComboBox | None = None
        self._visible_checkbox: QCheckBox | None = None
        self._results_tree: QTreeWidget | None = None
        self._result_items: list[dict[str, Any]] = []
        self._results_timer = QTimer(self)
        self._results_timer.setSingleShot(True)
        self._results_timer.setInterval(250)
        self._results_timer.timeout.connect(self._refresh_results)

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("Filter Criteria")
        self.setStyleSheet(APP_THEME.container_qss())
        if self._readonly:
            self.resize(600, 480)
            self.setMinimumSize(500, 350)
        else:
            self.resize(850, 700)
            self.setMinimumSize(600, 500)

        self._build_ui()
        self._populate()

    @property
    def original_name(self) -> str:
        """Name the filter had when the dialog opened; lets callers detect renames."""
        return self._filter_name

    @property
    def tag_store(self) -> DbTags | None:
        return self._tag_store

    @tag_store.setter
    def tag_store(self, value: DbTags | None) -> None:
        self._tag_store = value
        if self._filter_table is not None:
            self._filter_table.tag_store = value

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header: title + close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title_label = QLabel("Filter Criteria", self)
        title_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size + 2))
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        close_button = ActionButton(
            self, icon_name="fa6s.xmark", tooltip="Close", icon_size=14
        )
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.reject)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        # Filter name field
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        name_label = QLabel("Name:", self)
        name_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        name_layout.addWidget(name_label)

        self._name_edit = NameWidget(self)
        self._name_edit.setText(self._filter_name)
        self._name_edit.setPlaceholderText("Enter filter name")
        if self._readonly or self._is_system:
            self._name_edit.setReadOnly(True)
        name_layout.addWidget(self._name_edit)
        layout.addLayout(name_layout)

        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(8)

        sort_label = QLabel("Sort:", self)
        sort_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        sort_layout.addWidget(sort_label)
        self._sort_combo = SelectComboBox(self)
        self._sort_combo.addItem("Default (use Folder sorting)", userData="default")
        self._sort_combo.addItem("Manual", userData="manual")
        self._sort_combo.addItem("Other (live)", userData="group")
        group_index = self._sort_combo.count() - 1
        model = self._sort_combo.model()
        if isinstance(model, QStandardItemModel):
            group_item = model.item(group_index)
            if group_item is not None:
                group_item.setEnabled(False)
        for label, value in (
            ("A-Z", "a_z"),
            ("Z-A", "z_a"),
            ("Last Played", "last_played"),
            ("Qty Played", "qty_played"),
        ):
            self._sort_combo.addItem(f"    {label}", userData=value)
        if self._readonly:
            self._sort_combo.setEnabled(False)
        else:
            self._sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        current_sort_index = self._sort_combo.findData(self._sort_option)
        self._sort_combo.setCurrentIndex(max(0, current_sort_index))
        APP_THEME.setup_combo_box(self._sort_combo)
        sort_layout.addWidget(self._sort_combo)

        # Group combobox
        group_label = QLabel("Group:", self)
        group_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        sort_layout.addWidget(group_label)
        self._group_combo = SelectComboBox(self)
        self._group_combo.setEditable(True)
        self._group_combo.setMinimumWidth(140)
        self._populate_group_combo()
        if self._readonly or self._is_system:
            self._group_combo.setEnabled(False)
        APP_THEME.setup_combo_box(self._group_combo)
        sort_layout.addWidget(self._group_combo)

        # Visible checkbox (always editable, even for system filters)
        self._visible_checkbox = QCheckBox("Visible", self)
        self._visible_checkbox.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size)
        )
        self._visible_checkbox.setChecked(self._is_visible)
        if self._readonly:
            self._visible_checkbox.setEnabled(False)
        APP_THEME.setup_checkbox(self._visible_checkbox)
        sort_layout.addWidget(self._visible_checkbox)

        sort_layout.addStretch(1)
        layout.addLayout(sort_layout)

        if not self._readonly and not self._is_system:
            layout.addLayout(self._build_add_criteria_row())

        # Filter criteria table in scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._filter_table = FolderFilterTable(
            self.genres,
            self.media_configs,
            tags=self.tags,
            tag_store=self._tag_store,
            state=self._state,
            readonly=self._readonly or self._is_system,
        )
        scroll.setWidget(self._filter_table)
        layout.addWidget(scroll, 1)

        if not self._readonly:
            results_label = QLabel("Matched Results", self)
            results_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
            layout.addWidget(results_label)

            self._results_tree = QTreeWidget(self)
            self._results_tree.setColumnCount(2)
            self._results_tree.setHeaderLabels(["Folder / Video", "Manual order"])
            self._results_tree.setRootIsDecorated(False)
            self._results_tree.setAlternatingRowColors(True)
            self._results_tree.setMinimumHeight(190)
            self._results_tree.setDragDropMode(
                QAbstractItemView.DragDropMode.InternalMove
            )
            self._results_tree.setDefaultDropAction(Qt.DropAction.MoveAction)
            self._results_tree.setDropIndicatorShown(True)
            self._results_tree.header().setStretchLastSection(False)
            self._results_tree.header().setSectionResizeMode(
                0, self._results_tree.header().ResizeMode.Stretch
            )
            self._results_tree.header().setSectionResizeMode(
                1, self._results_tree.header().ResizeMode.ResizeToContents
            )
            self._results_tree.setDragEnabled(True)
            self._results_tree.setAcceptDrops(True)
            self._results_tree.setDragDropOverwriteMode(False)
            self._results_tree.model().rowsMoved.connect(self._on_results_moved)
            layout.addWidget(self._results_tree, 2)

        # Bottom button bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        if not self._readonly:
            save_button = ActionButton(self, icon_name="fa6s.check", tooltip="Save")
            save_button.clicked.connect(self._on_save)
            button_layout.addWidget(save_button)

            cancel_button = ActionButton(self, icon_name="fa6s.xmark", tooltip="Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)

            if self._edit_mode and not self._is_system:
                delete_button = DelayedDeleteButton(self)
                delete_button.setIconSize(
                    QSize(APP_THEME.icon_size, APP_THEME.icon_size)
                )
                delete_button.setToolTip("Delete Filter")
                delete_button.clicked.connect(self._on_delete)
                button_layout.addWidget(delete_button)

            button_layout.addStretch(1)
        else:
            # Readonly mode: show Edit button at bottom-right
            button_layout.addStretch(1)
            edit_btn = ActionButton(
                self, icon_name="fa6s.pen-to-square", tooltip="Edit Filter"
            )
            edit_btn.clicked.connect(
                lambda: self.edit_requested.emit(self._filter_name)
            )
            button_layout.addWidget(edit_btn)

        layout.addLayout(button_layout)

    def _build_add_criteria_row(self) -> QHBoxLayout:
        """Criteria type picker + add button so new criteria can be added inline."""
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)

        criteria_label = QLabel("Criteria:", self)
        criteria_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        add_layout.addWidget(criteria_label)

        self._criteria_type_combo = SelectComboBox(self)
        self._criteria_type_combo.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size)
        )
        self._criteria_type_combo.setMinimumWidth(200)
        self._criteria_type_combo.addItem("- Select a Criteria -", userData="")
        under_group = False
        for filter_type in FolderFilterTable.FILTER_TYPES:
            if filter_type in FolderFilterTable.FILTER_GROUP_HEADERS:
                self._criteria_type_combo.addItem(filter_type)
                index = self._criteria_type_combo.count() - 1
                model = self._criteria_type_combo.model()
                if model is not None and isinstance(model, QStandardItemModel):
                    item = model.item(index)
                    if item is not None:
                        item.setEnabled(False)
                under_group = True
            elif under_group:
                self._criteria_type_combo.addItem("    " + filter_type)
            else:
                self._criteria_type_combo.addItem(filter_type)
        # Apply grouped delegate for extra height on group headers
        self._criteria_type_combo.setItemDelegate(
            GroupedComboBoxDelegate(
                FolderFilterTable.FILTER_GROUP_HEADERS, self._criteria_type_combo
            )
        )
        APP_THEME.setup_combo_box(self._criteria_type_combo)
        add_layout.addWidget(self._criteria_type_combo)

        add_criteria_button = ActionButton(
            self, icon_name="fa6s.circle-plus", tooltip="Add Criteria"
        )
        add_criteria_button.clicked.connect(self._on_add_criteria)
        add_layout.addWidget(add_criteria_button)
        add_layout.addStretch(1)
        return add_layout

    def _on_add_criteria(self) -> None:
        table = self._filter_table
        combo = self._criteria_type_combo
        if table is None or combo is None:
            return
        table.add_filter(combo.currentText(), "")
        table._check_empty_state()
        # Start editing the new value cell so the user can type right away
        row = table.rowCount() - 1
        item = table.item(row, 1)
        if item is not None and item.flags() & Qt.ItemFlag.ItemIsEditable:
            table.setCurrentCell(row, 1)
            table.editItem(item)

    def _commit_pending_edit(self) -> None:
        """Commit an open cell editor; tool buttons don't take focus, so it would be lost."""
        table = self._filter_table
        if table is None:
            return
        if table.state() != QAbstractItemView.State.EditingState:
            return
        # indexWidget() also returns the active delegate editor for the index
        editor = table.indexWidget(table.currentIndex())
        if editor is not None:
            table.commitData(editor)
            table.closeEditor(editor, QAbstractItemDelegate.EndEditHint.NoHint)

    def _populate(self) -> None:
        """Populate the filter table with initial criteria."""
        table = self._filter_table
        if table is not None:
            for filter_item in self._initial_filters:
                table.add_filter(filter_item["filter"], filter_item["value"])
            table._check_empty_state()
            table.cellChanged.connect(self._schedule_results_refresh)
            table.model().rowsInserted.connect(self._schedule_results_refresh)
            table.model().rowsRemoved.connect(self._schedule_results_refresh)
        self._refresh_results()

    def _filter_store(self):
        return getattr(self._state, "filter_store", None)

    def _populate_group_combo(self) -> None:
        """Populate the Group combobox with available filter groups."""
        combo = self._group_combo
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("- None -", userData="")
        store = self._filter_store()
        if store is not None:
            try:
                groups = store.list_groups()
                for grp in groups:
                    # Exclude "Edited Recently" from the picker (settings-only)
                    if grp.get("name") == "Edited Recently":
                        continue
                    combo.addItem(grp["name"], userData=grp["group_id"])
                # Select the current group
                if self._group_id is not None:
                    idx = combo.findData(self._group_id)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
            except Exception:
                pass
        combo.blockSignals(False)

    def _get_selected_group_id(self) -> int | None:
        """Get the currently selected group ID from the combobox."""
        combo = self._group_combo
        if combo is None:
            return None
        data = combo.currentData()
        if data == "" or data is None:
            return None
        return int(data)

    def _on_sort_changed(self, _index: int) -> None:
        combo = self._sort_combo
        if combo is None:
            return
        sort_option = combo.currentData()
        if sort_option == "group":
            combo.setCurrentIndex(max(0, combo.findData(self._sort_option)))
            return
        self._sort_option = str(sort_option or "default")
        self._results_timer.stop()
        self._refresh_results()

    def _schedule_results_refresh(self, *_args: Any) -> None:
        self._results_timer.start()

    def _refresh_results(self, *_args: Any) -> None:
        tree = self._results_tree
        table = self._filter_table
        if tree is None or table is None:
            return
        filters = table.collect_filters()
        store = self._filter_store()
        db_filter = getattr(store, "db_filter", None)
        matches = (
            db_filter.matching_videos(
                filters,
                sort_option=(
                    self._sort_option if self._sort_option != "manual" else "default"
                ),
            )
            if db_filter is not None
            else []
        )

        if self._sort_option == "manual":
            current_by_identity = {
                (str(item["media_folder"]).casefold(), int(item["media_id"])): item
                for item in matches
            }
            ordered: list[dict[str, Any]] = []
            seen: set[tuple[str, int]] = set()
            for old_item in self._initial_manual_items:
                identity = (
                    str(old_item["media_folder"]).casefold(),
                    int(old_item["media_id"]),
                )
                match = current_by_identity.get(identity)
                item = dict(match or old_item)
                if match is None:
                    root = str(item["media_folder"]).rstrip("/")
                    item["file_path"] = self._join_path(root, str(item["rel_path"]))
                    item["title"] = Path(str(item["rel_path"])).stem
                    item["status"] = "missing"
                else:
                    item["status"] = "exists"
                ordered.append(item)
                seen.add(identity)
            ordered.extend(
                item
                for item in matches
                if (str(item["media_folder"]).casefold(), int(item["media_id"]))
                not in seen
            )
            self._result_items = ordered
        else:
            self._result_items = matches

        self._populate_results_tree()

    @staticmethod
    def _join_path(root: str, relative_path: str) -> str:
        return f"{root.rstrip('/')}/{relative_path.lstrip('/')}"

    def _populate_results_tree(self) -> None:
        tree = self._results_tree
        if tree is None:
            return
        tree.blockSignals(True)
        tree.clear()
        manual_enabled = not self._readonly and self._sort_option == "manual"
        tree.setColumnHidden(1, not manual_enabled)
        previous_folder: str | None = None
        parent_item: QTreeWidgetItem | None = None
        for position, result in enumerate(self._result_items, start=1):
            file_path = str(result.get("file_path") or result.get("rel_path") or "")
            folder_path = str(Path(file_path).parent)
            if folder_path != previous_folder:
                parent_item = QTreeWidgetItem(
                    [Path(folder_path).name or folder_path, ""]
                )
                parent_item.setToolTip(0, folder_path)
                parent_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsDropEnabled
                )
                parent_item.setForeground(0, QColor(APP_THEME.config.color_text_muted))
                tree.addTopLevelItem(parent_item)
                previous_folder = folder_path
            if parent_item is None:
                continue
            status = str(result.get("status", "exists"))
            title = str(result.get("title") or Path(file_path).name)
            video_item = QTreeWidgetItem([title, ""])
            video_item.setData(0, Qt.ItemDataRole.UserRole, result)
            video_item.setToolTip(0, file_path)
            video_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | (
                    Qt.ItemFlag.ItemIsDragEnabled
                    if manual_enabled
                    else Qt.ItemFlag.NoItemFlags
                )
                | (
                    Qt.ItemFlag.ItemIsDropEnabled
                    if manual_enabled
                    else Qt.ItemFlag.NoItemFlags
                )
            )
            if status == "missing":
                video_item.setForeground(0, QColor(APP_THEME.config.color_text_muted))
                video_item.setToolTip(0, f"Missing: {file_path}")
            parent_item.addChild(video_item)

            if manual_enabled:
                controls = QWidget(tree)
                controls_layout = QHBoxLayout(controls)
                controls_layout.setContentsMargins(0, 0, 0, 0)
                spin = QSpinBox(controls)
                spin.setRange(1, max(len(self._result_items), 1))
                spin.setValue(position)
                spin.setToolTip("Sort position")
                spin.valueChanged.connect(
                    lambda value, row=result: self._move_to_position(row, value)
                )
                up_button = QPushButton("↑", controls)
                down_button = QPushButton("↓", controls)
                up_button.setToolTip("Move up")
                down_button.setToolTip("Move down")
                up_button.setEnabled(position > 1)
                down_button.setEnabled(position < len(self._result_items))
                up_button.clicked.connect(
                    lambda _checked=False, row=result: self._move_by(row, -1)
                )
                down_button.clicked.connect(
                    lambda _checked=False, row=result: self._move_by(row, 1)
                )
                controls_layout.addWidget(spin)
                controls_layout.addWidget(up_button)
                controls_layout.addWidget(down_button)
                tree.setItemWidget(video_item, 1, controls)
        tree.expandAll()
        tree.blockSignals(False)

    def _move_to_position(self, row: dict[str, Any], position: int) -> None:
        identity = (row["media_folder"], row["media_id"])
        current_index = next(
            (
                index
                for index, item in enumerate(self._result_items)
                if (item["media_folder"], item["media_id"]) == identity
            ),
            -1,
        )
        if current_index < 0:
            return
        moved = self._result_items.pop(current_index)
        self._result_items.insert(
            max(0, min(len(self._result_items), position - 1)), moved
        )
        self._initial_manual_items = list(self._result_items)
        self._populate_results_tree()

    def _move_by(self, row: dict[str, Any], direction: int) -> None:
        identity = (row["media_folder"], row["media_id"])
        current_index = next(
            (
                index
                for index, item in enumerate(self._result_items)
                if (item["media_folder"], item["media_id"]) == identity
            ),
            -1,
        )
        target = current_index + direction
        if current_index < 0 or target < 0 or target >= len(self._result_items):
            return
        self._result_items[current_index], self._result_items[target] = (
            self._result_items[target],
            self._result_items[current_index],
        )
        self._initial_manual_items = list(self._result_items)
        self._populate_results_tree()

    def _on_results_moved(
        self,
        _parent: QModelIndex,
        _start: int,
        _end: int,
        _destination: QModelIndex,
        _destination_row: int,
    ) -> None:
        QTimer.singleShot(0, self._capture_results_order)

    def _capture_results_order(self) -> None:
        tree = self._results_tree
        if tree is None:
            return
        ordered = []
        for parent_index in range(tree.topLevelItemCount()):
            parent = tree.topLevelItem(parent_index)
            if parent is None:
                continue
            for child_index in range(parent.childCount()):
                child = parent.child(child_index)
                if child is not None:
                    ordered.append(child.data(0, Qt.ItemDataRole.UserRole))
        if all(item is not None for item in ordered):
            self._result_items = ordered
            self._initial_manual_items = list(ordered)
            self._populate_results_tree()

    def set_filter_data(
        self,
        filter_name: str,
        filters: list[dict[str, str]],
        sort_option: str = "default",
        group_id: int | None = None,
        is_visible: bool = True,
    ) -> None:
        """Update the dialog with new filter data (used for readonly popup refresh)."""
        self._filter_name = filter_name
        self._sort_option = sort_option
        self._group_id = group_id
        self._is_visible = is_visible
        if self._name_edit is not None:
            self._name_edit.setText(filter_name)
        if self._sort_combo is not None:
            index = self._sort_combo.findData(sort_option)
            self._sort_combo.setCurrentIndex(max(0, index))
        if self._visible_checkbox is not None:
            self._visible_checkbox.setChecked(is_visible)
        self._populate_group_combo()
        table = self._filter_table
        if table is not None:
            table.setRowCount(0)
            for filter_item in filters:
                table.add_filter(filter_item["filter"], filter_item["value"])
            table._check_empty_state()
        self._results_timer.stop()
        self._refresh_results()

    def _on_save(self) -> None:
        self._commit_pending_edit()
        name = self._name_edit.text().strip() if self._name_edit is not None else ""
        if not name:
            if self._name_edit is not None:
                self._name_edit.setFocus()
            return

        # Validate name characters
        is_valid, error_msg = validate_name(name)
        if not is_valid:
            if self._name_edit is not None:
                self._name_edit.setFocus()
            QMessageBox.warning(self, "Invalid Filter Name", error_msg)
            return

        filters = (
            self._filter_table.collect_filters()
            if self._filter_table is not None
            else []
        )
        self._results_timer.stop()
        self._refresh_results()
        # Close first so listeners never rebuild UI while this dialog is still active
        self.accept()
        group_id = self._get_selected_group_id()
        is_visible = (
            self._visible_checkbox.isChecked()
            if self._visible_checkbox is not None
            else True
        )
        self.saved.emit(
            name,
            filters,
            self._sort_option,
            list(self._result_items),
            group_id,
            is_visible,
        )

    def _on_delete(self) -> None:
        # Delete the filter that was opened, even if the name field was edited
        name = self._filter_name
        if not name and self._name_edit is not None:
            name = self._name_edit.text().strip()
        self.reject()
        self.deleted.emit(name)

    def apply_theme(self) -> None:
        APP_THEME.refresh_theme(self)
        if self._filter_table is not None:
            self._filter_table.apply_theme()
