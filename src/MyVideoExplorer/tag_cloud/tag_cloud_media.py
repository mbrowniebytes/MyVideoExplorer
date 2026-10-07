from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from MyVideoExplorer.db.db_tags import DbTags
from MyVideoExplorer.db.models.tag_item import TagStateProtocol
from MyVideoExplorer.tag_cloud.tag_button import TagButton
from MyVideoExplorer.tag_cloud.tag_cloud_widget import (
    TagCloudWidget,
    get_tag_cloud_sort_mode,
    set_tag_cloud_sort_mode,
)
from MyVideoExplorer.tag_cloud.tag_picker_dialog import TagPickerDialog
from MyVideoExplorer.tag_cloud.tag_util import (
    get_contrast_text_color,
    validate_tag_name,
)
from MyVideoExplorer.theme.theme import APP_THEME

__all__ = ["QColorDialog", "TagCloudMedia", "TagPickerDialog", "TagStateProtocol"]


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
            self.state.tag_counts_changed.connect(self._refresh_cloud)
        self._refresh_cloud()
        self.set_enabled(False)

    @property
    def _cloud(self) -> TagCloudWidget | None:
        return self._popup.cloud if self._popup is not None else None

    @property
    def _new_tag_edit(self) -> QLineEdit | None:
        return self.new_tag_edit

    @property
    def new_tag_edit(self) -> QLineEdit | None:
        return self._popup.new_tag_edit if self._popup is not None else None

    @property
    def _popup_assigned_layout(self) -> QHBoxLayout | None:
        return self._popup.assigned_layout if self._popup is not None else None

    @property
    def tags(self) -> list[str]:
        return list(self._tags)

    def set_tags(self, tags: list[str] | None) -> None:
        self._tags = list(tags or [])
        catalog_tags = (
            self.tag_store.list_tags()
            if self.tag_store
            else (self.state.tags if self.state else [])
        )
        self._tag_colors = {
            item["tag"].casefold(): item.get("color", "#808080")
            for item in catalog_tags
        }
        self._clear_layout(self.tags_layout)
        self._render_assigned_tags(
            self.tags_layout, self.tags_container, vertical_rows=True
        )
        self._sync_popup_data()

    def set_enabled(self, enabled: bool) -> None:
        self.add_button.setEnabled(enabled)

    def apply_theme(self) -> None:
        self.setStyleSheet(APP_THEME.container_qss())
        if self._popup is not None:
            self._popup.setStyleSheet(APP_THEME.container_qss())

    def _show_tag_cloud(self) -> None:
        if self.state is None:
            return
        if self._popup is None:
            self._build_popup()
        self._sync_popup_data()
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
        self._popup.tag_selected.connect(self._on_tag_selected)
        self._popup.tag_created.connect(self._create_and_add_tag)
        self._popup.tag_removed.connect(self._remove_tag)
        self._popup.tag_color_changed.connect(self._change_catalog_tag_color)
        self._popup.tag_edited.connect(self._update_catalog_tag)

    def _sync_popup_data(self) -> None:
        if self._popup is None:
            return
        catalog_tags = (
            self.tag_store.list_tags()
            if self.tag_store
            else (self.state.tags if self.state else [])
        )
        counts = self.tag_store.get_tag_counts() if self.tag_store else {}
        self._popup.set_data(self._tags, self._tag_colors, catalog_tags, counts)

    def _refresh_cloud(self) -> None:
        self._sync_popup_data()

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
                f"QToolButton {{ color: {get_contrast_text_color(color)}; "
                f"background-color: {color}; border-radius: 4px; padding: 2px 4px; }}"
            )
            if vertical_rows:
                row.addStretch(1)
            row.addWidget(label)
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
        self._sync_popup_data()

    def _change_catalog_tag_color(self, tag: str, color: str) -> None:
        if self.tag_store is not None and self.tag_store.set_tag_color(tag, color):
            self._on_catalog_changed()

    def _update_catalog_tag(self, old_tag: str, new_tag: dict[str, Any]) -> None:
        if self.tag_store is not None and self.tag_store.update_catalog_tag(
            old_tag, new_tag["tag"], new_tag["color"]
        ):
            self._tags = [
                new_tag["tag"] if tag.casefold() == old_tag.casefold() else tag
                for tag in self._tags
            ]
            self._on_catalog_changed()

    def _on_catalog_changed(self) -> None:
        self.set_tags(self._tags)
        self._sync_popup_data()

    def _on_media_sort_changed(self, index: int) -> None:
        mode = self.sort_combo.itemData(index)
        set_tag_cloud_sort_mode(mode)
        self.set_tags(self._tags)
        if self._cloud is not None:
            self._cloud.sort_combo.setCurrentIndex(
                self._cloud.sort_combo.findData(mode)
            )

    def _on_tag_selected(self, tag: str) -> None:
        if tag.casefold() in {item.casefold() for item in self._tags}:
            return
        self.tag_added.emit(tag)
        self._sync_popup_data()
        if self._cloud is not None:
            self._cloud.set_selected_tags([])
        if self._popup is not None:
            self._popup.hide()

    def _create_and_add_tag(self, tag: str) -> None:
        if not tag:
            return
        is_valid, _ = validate_tag_name(tag)
        if not is_valid:
            if self._popup is not None:
                self._popup.new_tag_edit.setToolTip(
                    "Tag names must be alphanumeric only."
                )
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
                if self._popup is not None:
                    self._popup.new_tag_edit.setToolTip(
                        "A tag with this name already exists."
                    )
            return
        if self._popup is not None:
            self._popup.new_tag_edit.clear()
        self.tag_added.emit(tag)
        self._sync_popup_data()
        if self._popup is not None:
            self._popup.hide()
