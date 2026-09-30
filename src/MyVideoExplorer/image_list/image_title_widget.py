from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class ImageTitleWidget(QWidget):
    play_video_requested = Signal(object)

    def __init__(self, log_util: LogUtil, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.log_util = log_util
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 0, 15, 0)
        layout.setSpacing(6)

        self.title_label = QLabel("", parent=self)
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._apply_title_style()
        self.update_title("")

        self.help_icon = QLabel("?", parent=self)
        self.help_icon.setFixedSize(20, 20)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())

        self.help_icon.setToolTip(
            "Image Preview Usage:\n"
            "- Use Mouse Wheel to scroll through folders\n"
            "- Double click on image to play media\n"
            "- Right click to scroll through images in current folder"
        )
        self.help_icon.installEventFilter(self)

        self.play_video_button = QPushButton("▶", parent=self)
        self.play_video_button.setObjectName("image_title_play_video_button")
        self.play_video_button.setMinimumWidth(60)
        self.play_video_button.setMinimumHeight(28)
        self.play_video_button.setToolTip("Play Video")
        self.play_video_button.clicked.connect(
            lambda: self.play_video_requested.emit(
                SignalPayload(
                    data=None,
                    sender=self.__class__.__name__,
                    name="Play Video Requested",
                    description="Emitted when the image title play button is clicked.",
                    flow=SignalFlow.USER_INPUT,
                )
            )
        )
        self.play_video_button.setStyleSheet(APP_THEME.small_button_qss())

        actions_widget = QWidget(self)
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(0)
        actions_layout.addWidget(self.help_icon, 0, Qt.AlignmentFlag.AlignLeft)
        actions_layout.addStretch()
        actions_layout.addWidget(self.play_video_button, 0, Qt.AlignmentFlag.AlignRight)
        actions_widget.setFixedWidth(
            self.help_icon.width() + self.play_video_button.minimumWidth() + 24
        )
        self.actions_widget = actions_widget
        self.actions_layout = actions_layout

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.actions_widget)

    def update_title(self, title: str) -> None:
        if title == "":
            title = f"{' ':<40}"
        if self.title_label.text() == title:
            return
        self.title_label.setText(title)

    def apply_theme(self) -> None:
        # super().apply_theme()
        # Special variants still need manual application as ThemeManager uses default QSS
        self._apply_title_style()
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())
        self.play_video_button.setStyleSheet(APP_THEME.small_button_qss())

    def _apply_title_style(self) -> None:
        self.title_label.setStyleSheet(APP_THEME.title_label_qss())
        self.title_label.ensurePolished()
        self.title_label.setContentsMargins(0, 4, 0, 8)
        self.title_label.setMinimumHeight(self.title_label.fontMetrics().height() + 16)
