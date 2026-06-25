from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.media_info_section.media_info_section_definitions import (
    get_media_info_toolbar_section_definitions,
)
from MyVideoExplorer.theme.theme import APP_THEME


class MediaInfoToolbarWidget(QWidget):
    sig_section_visibility_toggle_requested = Signal(object)
    sig_play_video_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.current_view_mode = ""
        self.section_toggle_buttons_by_id: dict[str, QPushButton] = {}

        self.toolbar_layout = QHBoxLayout(self)
        self.toolbar_layout.setContentsMargins(0, 0, 0, 0)

    def rebuild_for_view_mode(self, view_mode: str) -> None:
        if self.current_view_mode == view_mode and self.toolbar_layout.count() > 0:
            return

        self.current_view_mode = view_mode
        self.section_toggle_buttons_by_id.clear()
        self._clear_toolbar_layout()

        for section_id, section_label in get_media_info_toolbar_section_definitions(
            view_mode
        ):
            self._add_section_toggle_button(section_id, section_label)

        self._add_play_button()

    def set_section_toggle_checked(self, section_id: str, is_checked: bool) -> None:
        section_toggle_button = self.section_toggle_buttons_by_id.get(section_id)
        if section_toggle_button is not None:
            section_toggle_button.setChecked(is_checked)

    def apply_theme(self) -> None:
        pass

    def _add_section_toggle_button(
        self, section_id: str, section_label: str
    ) -> QPushButton:
        section_toggle_button = QPushButton(section_label)
        section_toggle_button.setObjectName("media_info_toolbar_toggle_button")
        section_toggle_button.setCheckable(True)
        section_toggle_button.setChecked(True)
        # section_toggle_button.setFixedSize(100, 25)
        section_toggle_button.setMinimumWidth(100)
        section_toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        section_toggle_button.setStyleSheet(APP_THEME.small_button_qss())
        font = QFont(APP_THEME.font_family, APP_THEME.font_size - 8)
        section_toggle_button.setFont(font)

        section_toggle_button.clicked.connect(
            lambda _: self._on_section_toggle_clicked(section_id)
        )

        self.section_toggle_buttons_by_id[section_id] = section_toggle_button
        self.toolbar_layout.addWidget(section_toggle_button)
        return section_toggle_button

    def _on_section_toggle_clicked(self, section_id: str) -> None:
        self.sig_section_visibility_toggle_requested.emit(
            SignalPayload(
                data=section_id,
                sender=self.__class__.__name__,
                name="Section Visibility Toggle",
                description=f"Toggled visibility for section: {section_id}",
                flow=SignalFlow.USER_INPUT,
            )
        )

    def _add_play_button(self) -> QPushButton:
        play_video_button = QPushButton("▶")
        play_video_button.setObjectName("media_info_toolbar_play_button")
        play_video_button.setMinimumWidth(40)
        play_video_button.clicked.connect(
            lambda: self.sig_play_video_requested.emit(
                SignalPayload(
                    data=None,
                    sender=self.__class__.__name__,
                    name="Play Video Requested",
                    description="Emitted when play video button is clicked in toolbar.",
                    flow=SignalFlow.USER_INPUT,
                )
            )
        )

        self.toolbar_layout.addStretch(1)
        self.toolbar_layout.addWidget(play_video_button)
        return play_video_button

    def _clear_toolbar_layout(self) -> None:
        while self.toolbar_layout.count():
            layout_item = self.toolbar_layout.takeAt(0)
            layout_widget = layout_item.widget()

            if layout_widget is not None:
                layout_widget.deleteLater()
