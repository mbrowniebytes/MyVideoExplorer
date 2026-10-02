from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_cloud_widget import (
    TagCloudWidget,
    get_tag_cloud_sort_mode,
)
from MyVideoExplorer.tag_cloud.tag_util import (
    get_contrast_text_color,
    validate_tag_name,
)
from MyVideoExplorer.theme.theme import APP_THEME


class TagPickerDialog(QDialog):
    """Popup dialog for managing and selecting tags for a media item."""

    tag_selected = Signal(str)
    tag_created = Signal(str)
    tag_removed = Signal(str)
    tag_color_changed = Signal(str, str)
    tag_edited = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Select Tags")
        self.setStyleSheet(APP_THEME.container_qss())

        self._tags: list[str] = []
        self._tag_colors: dict[str, str] = {}
        self._tag_counts: dict[str, int] = {}
        self._all_catalog_tags: list[dict[str, Any]] = []

        layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Current tags", self))
        header_layout.addStretch(1)

        self.close_button = QToolButton(self)
        self.close_button.setIcon(
            APP_THEME.icon("fa6s.xmark", color=APP_THEME.text_color)
        )
        self.close_button.setProperty("preserve_custom_style", True)
        self.close_button.setIconSize(QSize(14, 14))
        self.close_button.setFixedSize(22, 22)
        self.close_button.setAutoRaise(True)
        self.close_button.setStyleSheet(
            "QToolButton { background: transparent; border: 0; padding: 2px; }"
        )
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setToolTip("Close")
        self.close_button.clicked.connect(self.close)
        header_layout.addWidget(self.close_button)
        layout.addLayout(header_layout)

        self.assigned_container = QWidget(self)
        self.assigned_layout = QHBoxLayout(self.assigned_container)
        self.assigned_layout.setContentsMargins(0, 0, 0, 0)
        self.assigned_layout.setSpacing(4)
        layout.addWidget(self.assigned_container)

        layout.addWidget(QLabel("Available tags", self))
        self.cloud = TagCloudWidget(
            editable=True, selectable=True, color_editable=True, parent=self
        )
        self.cloud.tag_selected.connect(self._on_cloud_tag_selected)
        self.cloud.tag_color_changed.connect(self._on_cloud_tag_color_changed)
        self.cloud.tag_edited.connect(self._on_cloud_tag_edited)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.cloud)
        layout.addWidget(scroll, 1)

        create_row = QHBoxLayout()
        self.new_tag_edit = QLineEdit(self)
        self.new_tag_edit.setPlaceholderText("Create a new tag")
        self.create_button = QPushButton("Create and Add", self)
        self.create_button.clicked.connect(self._on_create_and_add)
        self.new_tag_edit.returnPressed.connect(self._on_create_and_add)
        create_row.addWidget(self.new_tag_edit, 1)
        create_row.addWidget(self.create_button)
        layout.addLayout(create_row)

        self._render_assigned_tags()

    def set_data(
        self,
        tags: list[str],
        tag_colors: dict[str, str],
        all_catalog_tags: list[dict[str, Any]],
        tag_counts: dict[str, int],
    ) -> None:
        self._tags = list(tags)
        self._tag_colors = dict(tag_colors)
        self._all_catalog_tags = list(all_catalog_tags)
        self._tag_counts = dict(tag_counts)
        self._render_assigned_tags()
        self._refresh_cloud()

    def _render_assigned_tags(self) -> None:
        self._clear_layout(self.assigned_layout)
        tags = list(self._tags)
        if get_tag_cloud_sort_mode() == TagCloudWidget.SORT_QUANTITY:
            tags.sort(
                key=lambda tag: (
                    -self._tag_counts.get(tag.casefold(), 0),
                    tag.casefold(),
                )
            )
        else:
            tags.sort(key=str.casefold)

        if not tags:
            self.assigned_layout.addWidget(QLabel("—", self.assigned_container))
        for tag in tags:
            row_widget = QWidget(self.assigned_container)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(4)
            color = self._tag_colors.get(tag.casefold(), "#808080")
            label = TagButton(row_widget)
            label.setText(tag)
            label.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            label.setToolTip(f"Double-click to edit {tag}")
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setStyleSheet(
                f"QToolButton {{ color: {get_contrast_text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 4px; }}"
            )
            label.double_clicked.connect(
                lambda current_tag=tag, current_row=row_widget: (
                    self._edit_assigned_tag(current_tag, current_row)
                )
            )
            row.addWidget(label)

            color_button = QToolButton(row_widget)
            color_button.setProperty("preserve_custom_style", True)
            color_button.setIcon(
                APP_THEME.icon(
                    "fa6s.palette",
                    color=get_contrast_text_color(color),
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
                lambda checked=False, name=tag: self.tag_removed.emit(name)
            )
            row.addWidget(remove_button)

            self.assigned_layout.addWidget(row_widget)
        self.assigned_layout.addStretch(1)

    def _edit_assigned_tag(self, tag: str, row_widget: QWidget) -> None:
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
                color=get_contrast_text_color(current_color),
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
        cancel_button.clicked.connect(self._render_assigned_tags)

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
                color=get_contrast_text_color(color_value),
            )
        )
        button.setStyleSheet(
            f"QToolButton {{ background-color: {color_value}; "
            "border: 1px solid palette(mid); border-radius: 3px; padding: 2px; }"
        )

    def _choose_assigned_color(self, tag: str, current_color: str) -> None:
        color = QColorDialog.getColor(QColor(current_color), self, "Choose Tag Color")
        if color.isValid():
            self.tag_color_changed.emit(tag, color.name())

    def _save_popup_assigned_tag(
        self, old_name: str, name_edit: QLineEdit, color_button: QToolButton
    ) -> None:
        new_name = name_edit.text().strip()
        is_valid, error_msg = validate_tag_name(new_name)
        if not is_valid:
            name_edit.setToolTip(error_msg)
            return

        if any(
            item["tag"].casefold() == new_name.casefold()
            and item["tag"].casefold() != old_name.casefold()
            for item in self._all_catalog_tags
        ):
            name_edit.setToolTip("Enter a unique tag name.")
            return

        color = str(color_button.property("tag_color"))
        self.tag_edited.emit(old_name, {"tag": new_name, "color": color})

    def _refresh_cloud(self) -> None:
        assigned = {current.casefold() for current in self._tags}
        self.cloud.set_tags(
            [
                {**tag, "qty": self._tag_counts.get(tag["tag"].casefold(), 0)}
                for tag in self._all_catalog_tags
                if tag["tag"].casefold() not in assigned
            ]
        )

    def _on_cloud_tag_selected(self, tag: str, selected: bool) -> None:
        if not selected or tag.casefold() in {item.casefold() for item in self._tags}:
            return
        self.tag_selected.emit(tag)
        self.cloud.set_selected_tags([])
        self.hide()

    def _on_cloud_tag_color_changed(self, tag: str, color: str) -> None:
        self.tag_color_changed.emit(tag, color)

    def _on_cloud_tag_edited(self, old_tag: str, new_tag: dict[str, Any]) -> None:
        self.tag_edited.emit(old_tag, new_tag)

    def _on_create_and_add(self) -> None:
        tag = self.new_tag_edit.text().strip()
        is_valid, error_msg = validate_tag_name(tag)
        if not is_valid:
            self.new_tag_edit.setToolTip(error_msg)
            return
        self.tag_created.emit(tag)

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.deleteLater()
