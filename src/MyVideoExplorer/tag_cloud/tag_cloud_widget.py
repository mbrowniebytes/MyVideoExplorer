from __future__ import annotations

from math import sqrt
from typing import Any

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QColorDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.models.tag_item import TagItem
from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_util import (
    get_contrast_text_color,
    style_painter_button,
    validate_tag_name,
)
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.widgets.buttons.action_button import ActionButton
from MyVideoExplorer.widgets.buttons.delayed_delete_button import DelayedDeleteButton
from MyVideoExplorer.widgets.combo_boxes.select_combo_box import SelectComboBox
from MyVideoExplorer.widgets.flow_layout import FlowLayout
from MyVideoExplorer.widgets.name_widget import NameWidget

_TAG_CLOUD_SORT_MODE = "Name"


def get_tag_cloud_sort_mode() -> str:
    return _TAG_CLOUD_SORT_MODE


def set_tag_cloud_sort_mode(mode: str) -> None:
    global _TAG_CLOUD_SORT_MODE
    if mode in (TagCloudWidget.SORT_NAME, TagCloudWidget.SORT_QUANTITY):
        _TAG_CLOUD_SORT_MODE = mode


class TagCloudWidget(QWidget):
    """Reusable tag cloud with filtering, sorting, selection, and optional editing."""

    changed = Signal()
    tag_selected = Signal(str, bool)
    tag_added = Signal(object)
    tag_edited = Signal(str, object)
    tag_deleted = Signal(str)
    tag_color_changed = Signal(str, str)
    tag_search_requested = Signal(str)

    SORT_NAME = "Name"
    SORT_QUANTITY = "Quantity"
    MIN_FONT_SIZE = 10
    MAX_FONT_SIZE = 24

    def __init__(
        self,
        tags: list[dict[str, Any] | TagItem] | None = None,
        *,
        editable: bool = False,
        selectable: bool = False,
        color_editable: bool = False,
        deletable: bool = False,
        show_search_button: bool = False,
        show_add_button: bool = False,
        confirm_delete_at_count: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.editable = editable
        self.selectable = selectable
        self.color_editable = color_editable
        self.deletable = deletable
        self.show_search_button = show_search_button
        self.show_add_button = show_add_button
        if confirm_delete_at_count is not None and confirm_delete_at_count < 1:
            raise ValueError("confirm_delete_at_count must be positive.")
        self.confirm_delete_at_count = confirm_delete_at_count
        self._tags: list[dict[str, Any]] = []
        self._selected_tags: set[str] = set()
        self._tag_widgets: list[tuple[dict[str, Any], QWidget]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        controls = QHBoxLayout()
        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("Search tags")
        self.sort_combo = SelectComboBox(self)
        self.sort_combo.addItem("A-Z", self.SORT_NAME)
        self.sort_combo.addItem("0-9", self.SORT_QUANTITY)
        self.sort_combo.setCurrentIndex(
            self.sort_combo.findData(get_tag_cloud_sort_mode())
        )
        controls.addWidget(self.filter_edit, 1)
        controls.addWidget(QLabel("Sort:", self))
        controls.addWidget(self.sort_combo)
        if self.show_add_button:
            self.add_tag_button = ActionButton(
                self, icon_name="fa6s.circle-plus", tooltip="Add new tag"
            )
            self.add_tag_button.setObjectName("add_tag_button")
            self.add_tag_button.clicked.connect(self._begin_add_tag)
            controls.addWidget(self.add_tag_button)
        layout.addLayout(controls)

        self.cloud_container = QWidget(self)
        self.cloud_layout = FlowLayout(self.cloud_container)
        self.cloud_container.setLayout(self.cloud_layout)
        layout.addWidget(self.cloud_container)

        self.filter_edit.textChanged.connect(self.refresh)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.set_tags(tags or [])

    @property
    def tags(self) -> list[dict[str, Any]]:
        return [dict(tag) for tag in self._tags]

    @property
    def selected_tags(self) -> list[str]:
        return [
            tag["tag"]
            for tag in self._tags
            if tag["tag"].casefold() in self._selected_tags
        ]

    def set_selected_tags(self, selected_tags: list[str]) -> None:
        self._selected_tags = {tag.casefold() for tag in selected_tags}
        self.refresh()

    def set_tags(self, tags: list[dict[str, Any] | TagItem]) -> None:
        normalized: list[dict[str, Any]] = []
        for item in tags:
            if isinstance(item, TagItem):
                tag_dict = item.to_dict()
            elif isinstance(item, dict):
                tag_dict = item
            else:
                continue
            tag_name = str(tag_dict.get("tag", "")).strip()
            if tag_name:
                normalized.append(
                    {
                        "tag": tag_name,
                        "color": str(tag_dict.get("color", "#808080")),
                        "qty": max(0, int(tag_dict.get("qty", 0) or 0)),
                    }
                )
        self._tags = normalized
        self.refresh()

    def _begin_add_tag(self) -> None:
        for tag, chip in self._tag_widgets:
            name_edit = chip.findChild(QLineEdit, "edit_tag_name")
            if not tag["tag"] and name_edit is not None:
                name_edit.setFocus()
                return

        tag: dict[str, Any] = {"tag": "", "color": "#808080", "qty": 0}
        chip = self._make_chip(tag, 0)
        self.cloud_layout.addWidget(chip)
        self._tag_widgets.append((tag, chip))
        chip.show()
        self._edit_chip(chip, tag, is_new=True)

    def refresh(self) -> None:
        while self.cloud_layout.count():
            item = self.cloud_layout.takeAt(0)
            if item:
                w = item.widget()
                if w is not None:
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()

        query = self.filter_edit.text().strip().casefold()
        tags = [tag for tag in self._tags if query in tag["tag"].casefold()]
        if self.sort_combo.currentData() == self.SORT_QUANTITY:
            tags.sort(key=lambda tag: (-tag["qty"], tag["tag"].casefold()))
        else:
            tags.sort(key=lambda tag: tag["tag"].casefold())

        maximum_qty = max((tag["qty"] for tag in tags), default=0)
        self._tag_widgets = []
        for tag in tags:
            chip = self._make_chip(tag, maximum_qty)
            chip.show()
            self.cloud_layout.addWidget(chip)
            self._tag_widgets.append((tag, chip))

        target_w = self.cloud_container.width()
        parent = self.parentWidget()
        if target_w <= 50 and parent is not None:
            target_w = parent.width()
        if target_w <= 50:
            target_w = 400
        target_h = self.cloud_layout.heightForWidth(max(target_w, 50))
        self.cloud_layout.setGeometry(QRect(0, 0, max(target_w, 50), max(target_h, 30)))
        self.cloud_container.updateGeometry()

    def _make_chip(self, tag: dict[str, Any], maximum_qty: int) -> QWidget:
        chip = QWidget(self.cloud_container)
        layout = QHBoxLayout(chip)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(5)

        size = self.MIN_FONT_SIZE
        if maximum_qty:
            size = round(
                self.MIN_FONT_SIZE
                + (self.MAX_FONT_SIZE - self.MIN_FONT_SIZE)
                * sqrt(tag["qty"] / maximum_qty)
            )
        label = TagButton(chip)
        label.setText(f"{tag['tag']} ({tag['qty']})")
        label.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        label.setCheckable(self.selectable)
        label.setChecked(tag["tag"].casefold() in self._selected_tags)
        if self.selectable:
            label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.setFont(QFont(self.font().family(), size))
        label.setStyleSheet(
            f"QToolButton {{ color: {self._text_color(tag['color'])}; "
            f"background-color: {tag['color']}; border: 0; border-radius: 5px; padding: 3px 5px; }}"
        )
        label.clicked.connect(
            lambda checked=False, name=tag["tag"]: self._on_tag_selected(name, checked)
        )
        if self.editable:
            label.setToolTip("Double-click to edit this tag")
            label.double_clicked.connect(lambda: self._edit_chip(chip, tag))
        layout.addWidget(label)

        if self.color_editable and not self.editable:
            color_button = ActionButton(
                chip,
                icon_name="fa6s.palette",
                icon_color=self._text_color(tag["color"]),
                tooltip=f"Change {tag['tag']} color",
                icon_size=14,
            )
            color_button.setProperty("tag_color", tag["color"])
            color_button.setFixedSize(24, 24)
            self._style_painter_button(color_button, tag["color"])
            color_button.clicked.connect(
                lambda checked=False, button=color_button, tag_data=tag: (
                    self._choose_tag_color(button, tag_data)
                )
            )
            layout.addWidget(color_button)

        if self.editable:
            edit_color_button = ActionButton(
                chip,
                icon_name="fa6s.palette",
                icon_color=self._text_color(tag["color"]),
                tooltip=f"Change {tag['tag']} color",
                icon_size=14,
            )
            edit_color_button.setProperty("tag_color", tag["color"])
            edit_color_button.setObjectName("edit_tag_color")
            self._style_painter_button(edit_color_button, tag["color"])
            edit_color_button.clicked.connect(
                lambda checked=False, button=edit_color_button, tag_data=tag: (
                    self._choose_tag_color(button, tag_data)
                )
            )
            layout.addWidget(edit_color_button)

        if self.show_search_button:
            search_button = ActionButton(
                chip,
                icon_name="fa6s.magnifying-glass",
                tooltip=f"Search for {tag['tag']}",
                icon_size=14,
            )
            search_button.setObjectName("search_tag")
            search_button.setProperty("preserve_custom_style", True)
            search_button.setFixedSize(22, 22)
            search_button.setStyleSheet(
                "QToolButton { background: transparent; border: 1px solid transparent; padding: 2px; }"
            )
            search_button.clicked.connect(
                lambda checked=False, name=tag["tag"]: self.tag_search_requested.emit(
                    name
                )
            )
            layout.addWidget(search_button)

        if self.deletable:
            confirm_title = None
            confirm_message = None
            if (
                self.confirm_delete_at_count is not None
                and tag["qty"] >= self.confirm_delete_at_count
            ):
                confirm_title = "Delete tag?"
                confirm_message = (
                    f'The tag "{tag["tag"]}" is used by {tag["qty"]} media items. '
                    "Are you sure you want to delete it?"
                )
            delete_button = DelayedDeleteButton(
                chip,
                confirmation_title=confirm_title,
                confirmation_message=confirm_message,
            )
            delete_button.setProperty("preserve_custom_style", True)
            delete_button.setIconSize(QSize(14, 14))
            delete_button.setFixedSize(22, 22)
            delete_button.setAutoRaise(True)
            delete_button.setStyleSheet(
                "QToolButton { background: transparent; border: 0; padding: 2px; }"
            )
            delete_button.setToolTip(f"Delete {tag['tag']}")
            delete_button.clicked.connect(
                lambda checked=False, name=tag["tag"]: self._delete_tag(name)
            )
            layout.addWidget(delete_button)
        return chip

    def _edit_chip(
        self, chip: QWidget, tag: dict[str, Any], *, is_new: bool = False
    ) -> None:
        layout = chip.layout()
        if layout is None:
            raise RuntimeError("Tag chip is missing its layout.")
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget() if item else None
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

        name_edit = NameWidget(chip)
        name_edit.setObjectName("edit_tag_name")
        name_edit.setText(tag["tag"])
        name_edit.setMinimumWidth(100)
        color_button = ActionButton(
            chip,
            icon_name="fa6s.palette",
            icon_color=self._text_color(tag["color"]),
            tooltip="Choose tag color",
            icon_size=14,
        )
        color_button.setProperty("tag_color", tag["color"])
        color_button.setObjectName("edit_tag_color_inline")
        color_button.setFixedSize(22, 22)
        self._style_painter_button(color_button, tag["color"])
        color_button.clicked.connect(
            lambda checked=False, button=color_button: self._choose_color(button)
        )
        save_button = ActionButton(
            chip, icon_name="fa6s.floppy-disk", tooltip="Save tag", icon_size=14
        )
        save_button.setObjectName("save_tag_edit")
        save_button.setEnabled(bool(name_edit.text().strip()))
        cancel_button = ActionButton(
            chip, icon_name="fa6s.xmark", tooltip="Cancel editing", icon_size=14
        )

        layout.addWidget(name_edit)
        layout.addWidget(color_button)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)

        save_button.clicked.connect(
            lambda checked=False: self._save_edit(
                tag, name_edit, color_button, chip, is_new=is_new
            )
        )
        name_edit.textChanged.connect(
            lambda text: save_button.setEnabled(bool(text.strip()))
        )
        cancel_button.clicked.connect(self.refresh)
        if is_new:
            name_edit.setFocus()

    def _save_edit(
        self,
        tag: dict[str, Any],
        name_edit: QLineEdit,
        color_button: QToolButton,
        chip: QWidget,
        *,
        is_new: bool = False,
    ) -> None:
        new_name = name_edit.text().strip()
        is_valid, error_msg = validate_tag_name(new_name)
        if not is_valid:
            name_edit.setToolTip(error_msg)
            return

        if any(
            current is not tag and current["tag"].casefold() == new_name.casefold()
            for current in self._tags
        ):
            name_edit.setToolTip("Enter a unique tag name.")
            return

        original_name = tag["tag"]
        tag["tag"] = new_name
        tag["color"] = str(color_button.property("tag_color"))
        self.changed.emit()
        if is_new:
            self.tag_added.emit(dict(tag))
        else:
            self.tag_edited.emit(original_name, dict(tag))
        self.refresh()

    def _choose_color(self, button: QToolButton) -> None:
        color = QColorDialog.getColor(
            QColor(str(button.property("tag_color"))), self, "Choose Tag Color"
        )
        if not color.isValid():
            return
        button.setProperty("tag_color", color.name())
        button.setIcon(
            APP_THEME.icon("fa6s.palette", color=self._text_color(color.name()))
        )
        self._style_painter_button(button, color.name())

    def _choose_tag_color(self, button: QToolButton, tag: dict[str, Any]) -> None:
        color = QColorDialog.getColor(
            QColor(str(button.property("tag_color"))), self, "Choose Tag Color"
        )
        if not color.isValid():
            return
        color_value = color.name()
        button.setProperty("tag_color", color_value)
        button.setIcon(
            APP_THEME.icon("fa6s.palette", color=self._text_color(color_value))
        )
        self._style_painter_button(button, color_value)
        tag["color"] = color_value
        self.changed.emit()
        self.tag_color_changed.emit(tag["tag"], color_value)

    def _style_painter_button(self, button: QToolButton, color: str) -> None:
        style_painter_button(button, color)

    def _delete_tag(self, tag_name: str) -> None:
        self._tags = [
            tag for tag in self._tags if tag["tag"].casefold() != tag_name.casefold()
        ]
        self._selected_tags.discard(tag_name.casefold())
        self.changed.emit()
        self.tag_deleted.emit(tag_name)
        self.refresh()

    def _on_tag_selected(self, tag_name: str, selected: bool) -> None:
        if selected:
            self._selected_tags.add(tag_name.casefold())
        else:
            self._selected_tags.discard(tag_name.casefold())
        self.tag_selected.emit(tag_name, selected)

    def _on_sort_changed(self, index: int) -> None:
        set_tag_cloud_sort_mode(self.sort_combo.itemData(index))
        self.refresh()

    @staticmethod
    def _text_color(color: str) -> str:
        return get_contrast_text_color(color)
