from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from MyVideoExplorer.media_info_section.media_info_section_definitions import MEDIA_INFO_SECTION_ACTORS
from MyVideoExplorer.theme.theme import APP_THEME


class MediaInfoScrollContentWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.section_widgets_by_id: dict[str, QFrame] = {}

        self.content_container_widget = QWidget()
        self.content_container_widget.setStyleSheet(APP_THEME.container_qss())

        self.section_layout = QVBoxLayout(self.content_container_widget)
        self.section_layout.setContentsMargins(0, 0, 0, 0)
        self.section_layout.setSpacing(4)
        self.section_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.content_container_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.outer_layout = QVBoxLayout(self)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.addWidget(self.scroll_area)

    def add_section_if_missing(self, section_id: str, section_widget: QFrame) -> None:
        if section_id in self.section_widgets_by_id:
            return

        self.section_widgets_by_id[section_id] = section_widget
        section_stretch = 1 if section_id == MEDIA_INFO_SECTION_ACTORS else 0
        self.section_layout.addWidget(section_widget, section_stretch)

    def remove_section_if_present(self, section_id: str) -> None:
        section_widget = self.section_widgets_by_id.pop(section_id, None)
        if section_widget is None:
            return

        self.section_layout.removeWidget(section_widget)
        section_widget.setParent(None)

    def toggle_section_visibility(self, section_id: str) -> bool | None:
        section_widget = self.section_widgets_by_id.get(section_id)
        if section_widget is None:
            return None

        next_visibility = not section_widget.isVisible()
        section_widget.setVisible(next_visibility)
        return next_visibility

    def clear_for_empty_nfo(self) -> None:
        self._clear_layout_without_deleting_persistent_widgets(self.section_layout)
        self.section_widgets_by_id.clear()

        empty_nfo_placeholder_label = QLabel("No NFO data found")
        empty_nfo_placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_nfo_placeholder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        empty_nfo_placeholder_label.setPixmap(QPixmap())
        empty_nfo_placeholder_label.setText("No NFO data found")

        self.section_layout.addWidget(empty_nfo_placeholder_label)

    def ensure_trailing_stretch(self) -> None:
        if self.section_layout.count() == 0:
            self.section_layout.addStretch()
            return

        last_layout_item = self.section_layout.itemAt(self.section_layout.count() - 1)
        if last_layout_item.spacerItem() is None:
            self.section_layout.addStretch()

    def apply_theme(self) -> None:
        self.content_container_widget.setStyleSheet(APP_THEME.container_qss())

    def _clear_layout_without_deleting_persistent_widgets(self, layout: QVBoxLayout) -> None:
        while layout.count():
            layout_item = layout.takeAt(0)
            layout_widget = layout_item.widget()
            child_layout = layout_item.layout()

            if layout_widget is not None:
                layout_widget.setParent(None)
            elif child_layout is not None:
                self._clear_layout_without_deleting_persistent_widgets(child_layout)
