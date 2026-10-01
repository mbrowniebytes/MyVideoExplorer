from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.tag_cloud.tag_cloud_widget import (
    TagButton,
    TagCloudWidget,
    get_tag_cloud_sort_mode,
    set_tag_cloud_sort_mode,
)
from MyVideoExplorer.theme.theme import APP_THEME


class TagStateProtocol(Protocol):
    tags: list[dict[str, str]]
    tags_changed: Any

    def add_tag(self, tag: str) -> Any: ...


class TagPickerDialog(QDialog):
    pass


class TagCloudMedia(QWidget):
    tag_added = Signal(str)
    tag_removed = Signal(str)

    def __init__(
        self,
        state: TagStateProtocol | None = None,
        tag_store: DbTags | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.state = state
        self.tag_store = tag_store
        self._tags: list[str] = []
        self._popup: TagPickerDialog | None = None
        self._cloud: TagCloudWidget | None = None
        self._new_tag_edit: QLineEdit | None = None
        self._popup_assigned_layout: QHBoxLayout | None = None
        self._tag_colors: dict[str, str] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel("Tags", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sort_combo = QComboBox(self)
        self.sort_combo.addItem("A-Z", TagCloudWidget.SORT_NAME)
        self.sort_combo.addItem("0-9", TagCloudWidget.SORT_QUANTITY)
        self.sort_combo.setCurrentIndex(
            self.sort_combo.findData(get_tag_cloud_sort_mode())
        )
        self.sort_combo.setToolTip("Sort tags by name or size")
        self.sort_combo.currentIndexChanged.connect(self._on_media_sort_changed)
        self.add_button = QToolButton(self)
        self.add_button.setObjectName("add_media_tag")
        self.add_button.setIcon(APP_THEME.icon("fa6s.tag", color=APP_THEME.text_color))
        self.add_button.setToolTip("Add a tag")
        self.add_button.setAccessibleName("Add a tag")
        self.add_button.setAutoRaise(True)
        self.add_button.clicked.connect(self._show_tag_cloud)

        self.tags_container = QWidget(self)
        self.tags_layout = QVBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(2)

        self.header_layout = QHBoxLayout()
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.sort_combo)
        self.header_layout.addWidget(self.add_button)
        layout.addLayout(self.header_layout)
        layout.addWidget(self.tags_container)
        self._render_assigned_tags(
            self.tags_layout, self.tags_container, vertical_rows=True
        )

        if self.state is not None:
            self.state.tags_changed.connect(self._on_catalog_changed)
        self._refresh_cloud()
        self.set_enabled(False)

    @property
    def tags(self) -> list[str]:
        return list(self._tags)

    def set_tags(self, tags: list[str] | None) -> None:
        self._tags = list(tags or [])
        self._tag_colors = {
            item["tag"].casefold(): item.get("color", "#808080")
            for item in (self.state.tags if self.state else [])
        }
        self._clear_layout(self.tags_layout)
        self._render_assigned_tags(
            self.tags_layout, self.tags_container, vertical_rows=True
        )
        if self._popup_assigned_layout is not None and self._popup is not None:
            self._clear_layout(self._popup_assigned_layout)
            self._render_assigned_tags(
                self._popup_assigned_layout,
                self._popup,
                vertical_rows=False,
                removable=True,
            )

    def set_enabled(self, enabled: bool) -> None:
        self.add_button.setEnabled(enabled)

    def _show_tag_cloud(self) -> None:
        if self.state is None:
            return
        if self._popup is None:
            self._build_popup()
        self._refresh_cloud()
        assert self._popup is not None
        self._popup.adjustSize()
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            self._popup.resize(
                min(max(500, self._popup.sizeHint().width()), available.width()),
                min(max(420, self._popup.sizeHint().height()), available.height()),
            )
        center_widget = self._media_container()
        if center_widget is not None:
            center = center_widget.rect().center()
            center = center_widget.mapToGlobal(center)
        elif screen is not None:
            center = screen.availableGeometry().center()
        else:
            center = self.mapToGlobal(self.rect().center())
        self._popup.move(
            center.x() - self._popup.width() // 2,
            center.y() - self._popup.height() // 2,
        )
        self._popup.setWindowModality(Qt.WindowModality.NonModal)
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

    def _build_popup(self) -> None:
        owner = self.window()
        self._popup = TagPickerDialog(owner)
        self._popup.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.WindowStaysOnTopHint
        )
        self._popup.setWindowTitle("Select Tags")
        layout = QVBoxLayout(self._popup)

        layout.addWidget(QLabel("Current tags", self._popup))
        assigned = QWidget(self._popup)
        self._popup_assigned_layout = QHBoxLayout(assigned)
        self._popup_assigned_layout.setContentsMargins(0, 0, 0, 0)
        self._popup_assigned_layout.setSpacing(4)
        self._render_assigned_tags(
            self._popup_assigned_layout,
            assigned,
            vertical_rows=False,
            removable=True,
        )
        layout.addWidget(assigned)

        layout.addWidget(QLabel("Available tags", self._popup))
        self._cloud = TagCloudWidget(
            editable=True, selectable=True, color_editable=True, parent=self._popup
        )
        self._cloud.tag_selected.connect(self._on_tag_selected)
        self._cloud.tag_color_changed.connect(self._change_catalog_tag_color)
        self._cloud.tag_edited.connect(self._update_catalog_tag)
        scroll = QScrollArea(self._popup)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cloud)
        layout.addWidget(scroll, 1)

        create_row = QHBoxLayout()
        self._new_tag_edit = QLineEdit(self._popup)
        self._new_tag_edit.setPlaceholderText("Create a new tag")
        create_button = QPushButton("Create and Add", self._popup)
        create_button.clicked.connect(self._create_and_add_tag)
        self._new_tag_edit.returnPressed.connect(self._create_and_add_tag)
        create_row.addWidget(self._new_tag_edit, 1)
        create_row.addWidget(create_button)
        layout.addLayout(create_row)

    def _refresh_cloud(self) -> None:
        if self._cloud is None:
            return
        tags = (
            self.tag_store.list_tags()
            if self.tag_store
            else self.state.tags
            if self.state
            else []
        )
        counts = self.tag_store.get_tag_counts() if self.tag_store else {}
        assigned = {current.casefold() for current in self._tags}
        self._cloud.set_tags(
            [
                {**tag, "qty": counts.get(tag["tag"].casefold(), 0)}
                for tag in tags
                if tag["tag"].casefold() not in assigned
            ]
        )

    def _media_container(self) -> QWidget | None:
        current = self.parentWidget()
        while current is not None:
            if isinstance(current, QTabWidget):
                return current.currentWidget()
            current = current.parentWidget()
        window = self.window()
        if isinstance(window, QMainWindow):
            return window.centralWidget()
        return None

    def _render_assigned_tags(
        self,
        layout: QHBoxLayout | QVBoxLayout,
        parent: QWidget,
        *,
        vertical_rows: bool,
        removable: bool = False,
    ) -> None:
        tags = list(self._tags)
        counts = self.tag_store.get_tag_counts() if self.tag_store else {}
        if get_tag_cloud_sort_mode() == TagCloudWidget.SORT_QUANTITY:
            tags.sort(key=lambda tag: (-counts.get(tag.casefold(), 0), tag.casefold()))
        else:
            tags.sort(key=str.casefold)
        if not tags:
            layout.addWidget(QLabel("—", parent))
        for tag in tags:
            row_widget = QWidget(parent)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            color = self._tag_colors.get(tag.casefold(), "#808080")
            label = TagButton(row_widget)
            label.setText(tag)
            label.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            label.setToolTip(tag)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setStyleSheet(
                f"QToolButton {{ color: {TagCloudWidget._text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 4px; }}"
            )
            if vertical_rows:
                row.addStretch(1)
            row.addWidget(label)
            if removable:
                label.setToolTip(f"Double-click to edit {tag}")
                label.double_clicked.connect(
                    lambda current_tag=tag, current_row=row_widget: (
                        self._edit_popup_assigned_tag(current_tag, current_row)
                    )
                )
            if removable:
                color_button = QToolButton(row_widget)
                color_button.setProperty("preserve_custom_style", True)
                color_button.setIcon(
                    APP_THEME.icon(
                        "fa6s.palette",
                        color=TagCloudWidget._text_color(color),
                    )
                )
                color_button.setStyleSheet(
                    f"QToolButton {{ background-color: {color}; "
                    "border: 1px solid palette(mid); border-radius: 3px; padding: 2px; }"
                )
                color_button.setFixedSize(24, 24)
                color_button.setCursor(Qt.CursorShape.PointingHandCursor)
                color_button.setToolTip(f"Change color for {tag}")
                color_button.clicked.connect(
                    lambda checked=False, name=tag, current=color: (
                        self._choose_assigned_color(name, current)
                    )
                )
                row.addWidget(color_button)
            if removable:
                remove_button = QToolButton(row_widget)
                remove_button.setIcon(
                    APP_THEME.icon("fa6s.trash-can", color=APP_THEME.text_color)
                )
                remove_button.setProperty("preserve_custom_style", True)
                remove_button.setIconSize(QSize(14, 14))
                remove_button.setFixedSize(22, 22)
                remove_button.setAutoRaise(True)
                remove_button.setStyleSheet(
                    "QToolButton { background: transparent; border: 0; padding: 2px; }"
                )
                remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
                remove_button.setToolTip(f"Remove {tag} from this media")
                remove_button.clicked.connect(
                    lambda checked=False, name=tag: self._remove_tag(name)
                )
                row.addWidget(remove_button)
            if not vertical_rows:
                row.addStretch(1)
            layout.addWidget(row_widget)
        if not vertical_rows:
            layout.addStretch(1)

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()

    def _remove_tag(self, tag: str) -> None:
        if tag.casefold() not in {current.casefold() for current in self._tags}:
            return
        self.tag_removed.emit(tag)
        self._refresh_cloud()

    def _edit_popup_assigned_tag(self, tag: str, row_widget: QWidget) -> None:
        if self.tag_store is None:
            return
        row = row_widget.layout()
        if row is None:
            raise RuntimeError("Assigned tag row is missing its layout.")
        while row.count():
            item = row.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()

        name_edit = QLineEdit(tag, row_widget)
        name_edit.setObjectName("edit_popup_assigned_tag_name")
        name_edit.setMinimumWidth(100)
        current_color = self._tag_colors.get(tag.casefold(), "#808080")
        color_button = QToolButton(row_widget)
        color_button.setProperty("preserve_custom_style", True)
        color_button.setObjectName("edit_popup_assigned_tag_color")
        color_button.setProperty("tag_color", current_color)
        color_button.setIcon(
            APP_THEME.icon(
                "fa6s.palette",
                color=TagCloudWidget._text_color(current_color),
            )
        )
        color_button.setStyleSheet(
            f"QToolButton {{ background-color: {current_color}; "
            "border: 1px solid palette(mid); border-radius: 3px; padding: 2px; }"
        )
        color_button.setFixedSize(24, 24)
        color_button.setToolTip("Choose tag color")
        color_button.clicked.connect(
            lambda checked=False, button=color_button: self._choose_popup_tag_color(
                button
            )
        )

        save_button = QToolButton(row_widget)
        save_button.setObjectName("save_popup_assigned_tag")
        save_button.setIcon(
            APP_THEME.icon("fa6s.floppy-disk", color=APP_THEME.text_color)
        )
        save_button.setToolTip("Save tag")
        save_button.setAutoRaise(True)
        cancel_button = QToolButton(row_widget)
        cancel_button.setIcon(APP_THEME.icon("fa6s.xmark", color=APP_THEME.text_color))
        cancel_button.setToolTip("Cancel editing")
        cancel_button.setAutoRaise(True)
        row.addWidget(name_edit)
        row.addWidget(color_button)
        row.addWidget(save_button)
        row.addWidget(cancel_button)
        save_button.clicked.connect(
            lambda checked=False: self._save_popup_assigned_tag(
                tag, name_edit, color_button
            )
        )
        cancel_button.clicked.connect(lambda: self.set_tags(self._tags))

    def _choose_popup_tag_color(self, button: QToolButton) -> None:
        color = QColorDialog.getColor(
            QColor(str(button.property("tag_color"))), self, "Choose Tag Color"
        )
        if not color.isValid():
            return
        color_value = color.name()
        button.setProperty("tag_color", color_value)
        button.setProperty("preserve_custom_style", True)
        button.setIcon(
            APP_THEME.icon(
                "fa6s.palette",
                color=TagCloudWidget._text_color(color_value),
            )
        )
        button.setStyleSheet(
            f"QToolButton {{ background-color: {color_value}; "
            "border: 1px solid palette(mid); border-radius: 3px; padding: 2px; }"
        )

    def _save_popup_assigned_tag(
        self, old_name: str, name_edit: QLineEdit, color_button: QToolButton
    ) -> None:
        if self.tag_store is None:
            return
        new_name = name_edit.text().strip()
        if not new_name or any(
            item["tag"].casefold() == new_name.casefold()
            and item["tag"].casefold() != old_name.casefold()
            for item in self.tag_store.list_tags()
        ):
            name_edit.setToolTip("Enter a unique tag name.")
            return
        color = str(color_button.property("tag_color"))
        if self.tag_store.update_catalog_tag(old_name, new_name, color):
            self._tags = [
                new_name if current.casefold() == old_name.casefold() else current
                for current in self._tags
            ]
            self._on_catalog_changed()

    def _change_catalog_tag_color(self, tag: str, color: str) -> None:
        if self.tag_store is not None and self.tag_store.set_tag_color(tag, color):
            self._on_catalog_changed()

    def _update_catalog_tag(self, old_tag: str, new_tag: dict) -> None:
        if self.tag_store is not None and self.tag_store.update_catalog_tag(
            old_tag, new_tag["tag"], new_tag["color"]
        ):
            self._tags = [
                new_tag["tag"] if tag.casefold() == old_tag.casefold() else tag
                for tag in self._tags
            ]
            self._on_catalog_changed()

    def _choose_assigned_color(self, tag: str, current_color: str) -> None:
        color = QColorDialog.getColor(QColor(current_color), self, "Choose Tag Color")
        if color.isValid():
            self._change_catalog_tag_color(tag, color.name())

    def _on_catalog_changed(self) -> None:
        self.set_tags(self._tags)
        self._refresh_cloud()

    def _on_media_sort_changed(self, index: int) -> None:
        mode = self.sort_combo.itemData(index)
        set_tag_cloud_sort_mode(mode)
        self.set_tags(self._tags)
        if self._cloud is not None:
            self._cloud.sort_combo.setCurrentIndex(
                self._cloud.sort_combo.findData(mode)
            )

    def _on_tag_selected(self, tag: str, selected: bool) -> None:
        if not selected or tag.casefold() in {item.casefold() for item in self._tags}:
            return
        self.tag_added.emit(tag)
        self._refresh_cloud()
        if self._cloud is not None:
            self._cloud.set_selected_tags([])
        if self._popup is not None:
            self._popup.hide()

    def _create_and_add_tag(self) -> None:
        if self._new_tag_edit is None:
            return
        tag = self._new_tag_edit.text().strip()
        if not tag:
            return
        added = (
            self.tag_store.add_catalog_tag(tag)
            if self.tag_store is not None
            else self.state.add_tag(tag)
            if self.state is not None
            else False
        )
        if not added:
            if self.state is not None and any(
                item["tag"].casefold() == tag.casefold() for item in self.state.tags
            ):
                self.tag_added.emit(tag)
                if self._popup is not None:
                    self._popup.hide()
            else:
                self._new_tag_edit.setToolTip("A tag with this name already exists.")
            return
        self._new_tag_edit.clear()
        self.tag_added.emit(tag)
        self._refresh_cloud()
        if self._popup is not None:
            self._popup.hide()
