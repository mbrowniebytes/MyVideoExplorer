from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.folder_filter.folder_filter_table import FolderFilterTable
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.combo_box_delegate import GroupedComboBoxDelegate

if TYPE_CHECKING:
    from MyVideoExplorer.db.db_tags import DbTags


class FilterCriteriaDialog(QDialog):
    """
    Modal dialog for viewing and editing filter criteria.

    Supports edit mode (pre-filled with save/cancel/delete) and add mode
    (empty with save/cancel only). Also supports readonly mode for display-only
    usage (e.g., the FolderFilters popup).
    """

    # Emitted when the user saves the filter
    saved = Signal(str, list)  # filter_name, filters_list
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
        edit_mode: bool = True,
        readonly: bool = False,
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
        self._edit_mode = edit_mode
        self._readonly = readonly

        self._name_edit: QLineEdit | None = None
        self._filter_table: FolderFilterTable | None = None
        self._criteria_type_combo: QComboBox | None = None

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("Filter Criteria")
        self.setStyleSheet(APP_THEME.container_qss())
        self.resize(600, 480)
        self.setMinimumSize(500, 350)

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

        close_button = QToolButton(self)
        close_button.setIcon(APP_THEME.icon("fa6s.xmark", color=APP_THEME.text_color))
        close_button.setIconSize(QSize(14, 14))
        close_button.setFixedSize(22, 22)
        close_button.setAutoRaise(True)
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.reject)
        header_layout.addWidget(close_button)
        layout.addLayout(header_layout)

        # Filter name field
        name_layout = QHBoxLayout()
        name_layout.setSpacing(8)
        name_label = QLabel("Name:", self)
        name_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        name_layout.addWidget(name_label)

        self._name_edit = QLineEdit(self._filter_name, self)
        self._name_edit.setPlaceholderText("Enter filter name")
        self._name_edit.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        if self._readonly:
            self._name_edit.setReadOnly(True)
        name_layout.addWidget(self._name_edit)
        layout.addLayout(name_layout)

        if not self._readonly:
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
            readonly=self._readonly,
        )
        scroll.setWidget(self._filter_table)
        layout.addWidget(scroll, 1)

        # Bottom button bar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        if not self._readonly:
            save_button = QToolButton(self)
            save_button.setIcon(
                APP_THEME.icon("fa6s.check", color=APP_THEME.text_color)
            )
            save_button.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
            save_button.setToolTip("Save")
            save_button.clicked.connect(self._on_save)
            button_layout.addWidget(save_button)

            cancel_button = QToolButton(self)
            cancel_button.setIcon(
                APP_THEME.icon("fa6s.xmark", color=APP_THEME.text_color)
            )
            cancel_button.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
            cancel_button.setToolTip("Cancel")
            cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(cancel_button)

            if self._edit_mode:
                delete_button = QToolButton(self)
                delete_button.setIcon(
                    APP_THEME.icon("fa6s.trash-can", color=APP_THEME.text_color)
                )
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
            edit_btn = QToolButton(self)
            edit_btn.setIcon(
                APP_THEME.icon("fa6s.pen-to-square", color=APP_THEME.text_color)
            )
            edit_btn.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
            edit_btn.setToolTip("Edit Filter")
            edit_btn.setAutoRaise(True)
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

        self._criteria_type_combo = QComboBox(self)
        self._criteria_type_combo.setFont(
            QFont(APP_THEME.font_family, APP_THEME.font_size)
        )
        self._criteria_type_combo.setMinimumWidth(200)
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

        add_criteria_button = QToolButton(self)
        add_criteria_button.setIcon(
            APP_THEME.icon("fa6s.circle-plus", color=APP_THEME.text_color)
        )
        add_criteria_button.setIconSize(QSize(APP_THEME.icon_size, APP_THEME.icon_size))
        add_criteria_button.setToolTip("Add Criteria")
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

    def set_filter_data(self, filter_name: str, filters: list[dict[str, str]]) -> None:
        """Update the dialog with new filter data (used for readonly popup refresh)."""
        if self._name_edit is not None:
            self._name_edit.setText(filter_name)
        table = self._filter_table
        if table is not None:
            table.setRowCount(0)
            for filter_item in filters:
                table.add_filter(filter_item["filter"], filter_item["value"])
            table._check_empty_state()

    def _on_save(self) -> None:
        self._commit_pending_edit()
        name = self._name_edit.text().strip() if self._name_edit is not None else ""
        if not name:
            if self._name_edit is not None:
                self._name_edit.setFocus()
            return
        filters = (
            self._filter_table.collect_filters()
            if self._filter_table is not None
            else []
        )
        # Close first so listeners never rebuild UI while this dialog is still active
        self.accept()
        self.saved.emit(name, filters)

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
