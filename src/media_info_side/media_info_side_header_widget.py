from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.theme.theme import APP_THEME


class MediaInfoSideHeaderWidget(QWidget):
    """Compact side header with quick actions for the selected media item."""

    sig_play_video_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.header_layout = QVBoxLayout(self)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(0)

        self.play_video_button = QPushButton("▶")
        self.play_video_button.setMinimumWidth(40)
        self.play_video_button.clicked.connect(self.sig_play_video_requested.emit)

        self.title_label = QLabel("NFO")
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.header_layout.addWidget(self.play_video_button)
        self.header_layout.addWidget(self.title_label)

        self.apply_theme()

    def apply_theme(self) -> None:
        self.play_video_button.setStyleSheet(APP_THEME.small_button_qss())
        self.title_label.setStyleSheet(APP_THEME.secondary_label_qss())
