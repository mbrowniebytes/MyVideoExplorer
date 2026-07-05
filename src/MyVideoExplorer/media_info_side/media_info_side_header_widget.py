from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from MyVideoExplorer.app.app_signals_model import SignalPayload, SignalFlow
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from MyVideoExplorer.theme.themable_mixin import ThemableMixin
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class MediaInfoSideHeaderWidget(QWidget, ThemableMixin):
    """Compact side header with quick actions for the selected media item."""

    sig_play_video_requested = Signal(object)

    def __init__(self, log_util: LogUtil | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_util = log_util or LogUtil()

        self.header_layout = QVBoxLayout(self)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(8)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.play_video_button = QPushButton("▶")
        self.play_video_button.setMinimumWidth(60)

        self.play_video_button.clicked.connect(
            lambda: self.sig_play_video_requested.emit(
                SignalPayload(
                    data=None,
                    sender=self.__class__.__name__,
                    name="Play Video Requested",
                    description="Emitted when play video button is clicked in side header.",
                    flow=SignalFlow.USER_INPUT,
                )
            )
        )

        self.title_label = QLabel("NFO")
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.header_layout.addWidget(self.play_video_button)
        self.header_layout.addWidget(self.title_label)

        self.apply_theme()

    def apply_theme(self) -> None:
        super().apply_theme()
        self.play_video_button.setStyleSheet(APP_THEME.small_button_qss())
        self.title_label.setStyleSheet(APP_THEME.secondary_label_qss())
