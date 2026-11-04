from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton
from MyVideoExplorer.widgets.name_widget import NameWidget


class SettingsFilterGroupsDialog(QDialog):
    """Dialog for managing filter groups: rename, delete, and view filter counts."""

    COL_EDIT = 0
    COL_NAME = 1
    COL_QTY = 2
    COL_DELETE = 3
    COLUMN_COUNT = 4

    def __init__(
        self,
        state: SettingsState,
        log_util: LogUtil,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.log_util = log_util
        self.setWindowTitle("Filter Groups")
        self.setStyleSheet(APP_THEME.container_qss())
        self.resize(500, 350)
        self.setMinimumSize(400, 250)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        self._table: QTableWidget | None = None
        self._editing_row: int | None = None

        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Filter Groups", self)
        title_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size + 2))
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # Table
        self._table = QTableWidget(self)
        self._table.setColumnCount(self.COLUMN_COUNT)
        self._table.setHorizontalHeaderLabels(["", "Name", "Filters", ""])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(APP_THEME.table_qss())

        header = self._table.horizontalHeader()
        header.setMinimumSectionSize(32)
        header.setSectionResizeMode(self.COL_EDIT, header.ResizeMode.Fixed)
        header.setSectionResizeMode(self.COL_NAME, header.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_QTY, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_DELETE, header.ResizeMode.Fixed)
        self._table.setColumnWidth(self.COL_EDIT, 32)
        self._table.setColumnWidth(self.COL_DELETE, 36)

        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table, 1)

        # Footer
        footer_layout = QHBoxLayout()
        add_group_btn = ActionButton(
            self, icon_name="fa6s.circle-plus", tooltip="Add New Group"
        )
        add_group_btn.clicked.connect(self._on_add_group)
        footer_layout.addWidget(add_group_btn)
        footer_layout.addStretch(1)
        close_btn = ActionButton(self, icon_name="fa6s.xmark", tooltip="Close")
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)

    def _refresh_list(self) -> None:
        table = self._table
        if table is None:
            return

        # Cancel any active inline edit
        if self._editing_row is not None:
            self._commit_inline_edit()

        table.setRowCount(0)
        try:
            groups = self.state.list_filter_groups()
        except Exception as e:
            self.log_util.error(f"Failed to load filter groups: {e}")
            return

        if not groups:
            table.setRowCount(1)
            placeholder = QTableWidgetItem("No filter groups found.")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(0, 0, placeholder)
            table.setSpan(0, 0, 1, self.COLUMN_COUNT)
            return

        cell_font = QFont(APP_THEME.font_family, APP_THEME.font_size - 4)
        table.setRowCount(len(groups))
        for row_idx, grp in enumerate(groups):
            group_id = grp["group_id"]
            name = grp["name"]
            is_system = grp["is_system"]
            filter_count = grp["filter_count"]

            # Edit button (hidden for system groups)
            if not is_system:
                edit_btn = ActionButton(
                    table, icon_name="fa6s.pen-to-square", tooltip=f"Rename '{name}'"
                )
                edit_btn.setIconSize(QSize(14, 14))
                edit_btn.clicked.connect(
                    lambda checked=False, r=row_idx: self._start_inline_edit(r)
                )
                table.setCellWidget(row_idx, self.COL_EDIT, edit_btn)

            # Name cell
            name_item = QTableWidgetItem(name)
            name_item.setFont(cell_font)
            if is_system:
                name_item.setForeground(QColor(APP_THEME.config.color_text_muted))
                name_item.setToolTip(f"{name} (system)")
            table.setItem(row_idx, self.COL_NAME, name_item)

            # Qty cell
            qty_item = QTableWidgetItem(str(filter_count))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_item.setFont(cell_font)
            table.setItem(row_idx, self.COL_QTY, qty_item)

            # Delete button (hidden for system groups)
            if not is_system:
                del_btn = DelayedDeleteButton(table, icon_name="fa6s.trash-can")
                del_btn.setIconSize(QSize(14, 14))
                del_btn.setToolTip(f"Delete group '{name}'")
                del_btn.clicked.connect(
                    lambda checked=False, gid=group_id: self._delete_group(gid)
                )
                table.setCellWidget(row_idx, self.COL_DELETE, del_btn)

    def _on_add_group(self) -> None:
        """Open a prompt to create a new filter group."""
        # Use a simple inline approach: add a new row with an edit widget
        table = self._table
        if table is None:
            return

        # Create a dialog-like input using a QLineEdit in a temporary widget
        input_widget = QWidget(self)
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(12, 8, 12, 8)
        input_layout.setSpacing(8)

        name_label = QLabel("New Group:", self)
        name_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        input_layout.addWidget(name_label)

        name_edit = NameWidget(self)
        name_edit.setPlaceholderText("Enter group name")
        input_layout.addWidget(name_edit, 1)

        ok_btn = ActionButton(self, icon_name="fa6s.check", tooltip="Create")
        ok_btn.setIconSize(QSize(14, 14))
        input_layout.addWidget(ok_btn)

        cancel_btn = ActionButton(self, icon_name="fa6s.xmark", tooltip="Cancel")
        cancel_btn.setIconSize(QSize(14, 14))
        input_layout.addWidget(cancel_btn)

        # Replace footer temporarily
        self._show_add_group_input(name_edit, ok_btn, cancel_btn)

    def _show_add_group_input(
        self, name_edit: QLineEdit, ok_btn: ActionButton, cancel_btn: ActionButton
    ) -> None:
        """Show the add group input in the footer area."""
        # Find the footer layout (last layout in the main layout)
        main_layout = self.layout()
        if main_layout is None:
            return

        # Remove the footer and replace with input
        footer_item = main_layout.takeAt(main_layout.count() - 1)
        if footer_item is not None:
            footer_layout_obj = footer_item.layout()
            if footer_layout_obj is not None:
                footer_layout_obj.deleteLater()

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(12, 0, 12, 0)
        name_label = QLabel("New Group:", self)
        name_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        footer_layout.addWidget(name_label)
        footer_layout.addWidget(name_edit, 1)
        footer_layout.addWidget(ok_btn)
        footer_layout.addWidget(cancel_btn)
        if isinstance(main_layout, QVBoxLayout):
            main_layout.addLayout(footer_layout)

        def on_create() -> None:
            new_name = name_edit.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "Group name cannot be empty.")
                return
            try:
                self.state.create_filter_group(new_name)
                self._refresh_list()
            except ValueError as e:
                QMessageBox.warning(self, "Create Failed", str(e))
            except Exception as e:
                self.log_util.error(f"Failed to create group: {e}")
                QMessageBox.critical(self, "Error", str(e))
            self._restore_footer()

        def on_cancel() -> None:
            self._restore_footer()

        ok_btn.clicked.disconnect()
        cancel_btn.clicked.disconnect()
        ok_btn.clicked.connect(on_create)
        cancel_btn.clicked.connect(on_cancel)
        name_edit.returnPressed.connect(on_create)
        name_edit.setFocus()

    def _restore_footer(self) -> None:
        """Restore the original footer with Add Group and Close buttons."""
        main_layout = self.layout()
        if main_layout is None:
            return

        # Remove the last layout (input footer)
        footer_item = main_layout.takeAt(main_layout.count() - 1)
        if footer_item is not None:
            footer_layout_obj = footer_item.layout()
            if footer_layout_obj is not None:
                footer_layout_obj.deleteLater()

        # Re-add the original footer
        footer_layout = QHBoxLayout()
        add_group_btn = ActionButton(
            self, icon_name="fa6s.circle-plus", tooltip="Add New Group"
        )
        add_group_btn.clicked.connect(self._on_add_group)
        footer_layout.addWidget(add_group_btn)
        footer_layout.addStretch(1)
        close_btn = ActionButton(self, icon_name="fa6s.xmark", tooltip="Close")
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        if isinstance(main_layout, QVBoxLayout):
            main_layout.addLayout(footer_layout)

    def _on_double_click(self, index) -> None:
        table = self._table
        if table is None:
            return
        row = index.row()
        col = index.column()
        if col == self.COL_NAME:
            # Check if this is a system group
            try:
                groups = self.state.list_filter_groups()
                if row < len(groups) and groups[row].get("is_system"):
                    return
            except Exception:
                pass
            self._start_inline_edit(row)

    def _start_inline_edit(self, row: int) -> None:
        table = self._table
        if table is None:
            return

        # Cancel any previous edit
        if self._editing_row is not None:
            self._commit_inline_edit()

        name_item = table.item(row, self.COL_NAME)
        if name_item is None:
            return
        current_name = name_item.text()

        # Create inline edit widget
        edit_widget = QWidget(table)
        edit_layout = QHBoxLayout(edit_widget)
        edit_layout.setContentsMargins(2, 0, 2, 0)
        edit_layout.setSpacing(4)

        line_edit = QLineEdit(edit_widget)
        line_edit.setText(current_name)
        line_edit.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size - 4))
        line_edit.returnPressed.connect(lambda: self._commit_inline_edit())

        save_btn = ActionButton(edit_widget, icon_name="fa6s.check", tooltip="Save")
        save_btn.setIconSize(QSize(12, 12))
        save_btn.clicked.connect(lambda: self._commit_inline_edit())

        cancel_btn = ActionButton(edit_widget, icon_name="fa6s.xmark", tooltip="Cancel")
        cancel_btn.setIconSize(QSize(12, 12))
        cancel_btn.clicked.connect(lambda: self._cancel_inline_edit())

        edit_layout.addWidget(line_edit, 1)
        edit_layout.addWidget(save_btn)
        edit_layout.addWidget(cancel_btn)

        table.setCellWidget(row, self.COL_NAME, edit_widget)
        self._editing_row = row

        # Store reference for commit
        edit_widget.setProperty("line_edit", line_edit)  # type: ignore[arg-type]
        QTimer.singleShot(50, line_edit.setFocus)
        QTimer.singleShot(50, line_edit.selectAll)

    def _commit_inline_edit(self) -> None:
        table = self._table
        row = self._editing_row
        if table is None or row is None:
            return

        widget = table.cellWidget(row, self.COL_NAME)
        if widget is None:
            self._editing_row = None
            return

        # Get the line edit from the widget
        line_edit: QLineEdit | None = None
        child = widget.findChild(QLineEdit)  # type: ignore[var-annotated]
        if child is not None:
            line_edit = child

        if line_edit is None:
            self._editing_row = None
            self._refresh_list()
            return

        new_name = line_edit.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Invalid Name", "Group name cannot be empty.")
            return

        # Find the group_id for this row
        groups = self.state.list_filter_groups()
        # We need to find the group by matching the original name (before edit)
        # Since we can't easily get the original name, use the row index
        if row < len(groups):
            grp = groups[row]
            old_name = grp["name"]
            if new_name.casefold() == old_name.casefold():
                # No change
                self._editing_row = None
                self._refresh_list()
                return

            try:
                self.state.rename_filter_group(grp["group_id"], new_name)
                self._editing_row = None
                self._refresh_list()
            except ValueError as e:
                QMessageBox.warning(self, "Rename Failed", str(e))
            except Exception as e:
                self.log_util.error(f"Failed to rename group: {e}")
                QMessageBox.critical(self, "Error", str(e))
        else:
            self._editing_row = None
            self._refresh_list()

    def _cancel_inline_edit(self) -> None:
        self._editing_row = None
        self._refresh_list()

    def _delete_group(self, group_id: int) -> None:
        try:
            self.state.delete_filter_group(group_id)
            self._refresh_list()
        except ValueError as e:
            QMessageBox.warning(self, "Delete Failed", str(e))
        except Exception as e:
            self.log_util.error(f"Failed to delete group: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def apply_theme(self) -> None:
        APP_THEME.refresh_theme(self)
        self._refresh_list()
