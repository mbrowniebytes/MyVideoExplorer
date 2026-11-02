from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QToolButton, QWidget

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.log_util import LogUtil


class ImageTitleWidget(QWidget):
    play_video_requested = Signal(object)
    video_player_requested = Signal(str)

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
        self.play_video_button.setFixedSize(48, 28)
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

        self._player_buttons: dict[str, QToolButton] = {}
        actions_widget = QWidget(self)
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(0)
        actions_layout.addWidget(self.help_icon, 0, Qt.AlignmentFlag.AlignLeft)
        actions_layout.addStretch()
        actions_layout.addWidget(self.play_video_button, 0, Qt.AlignmentFlag.AlignRight)
        self.actions_widget = actions_widget
        self.actions_layout = actions_layout
        self.set_video_players([])

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.actions_widget)

    def set_video_players(self, players: list[dict]) -> None:
        """Display configured player shortcuts after the system-default action."""
        for button in self._player_buttons.values():
            self.actions_layout.removeWidget(button)
            button.deleteLater()
        self._player_buttons.clear()

        icon_names = {
            "vlc": "fa6s.play",
            "potplayer": "fa6s.film",
            "mpc_qt": "fa6s.clapperboard",
            "custom": "fa6s.video",
        }
        for player in players:
            player_id = player.get("id")
            if (
                player_id not in icon_names
                or not player.get("show_icon")
                or not player.get("executable", "").strip()
            ):
                continue
            button = QToolButton(self.actions_widget)
            button.setObjectName(f"image_title_play_{player_id}_button")
            button.setAutoRaise(True)
            button.setProperty("preserve_custom_style", True)
            button.setFixedSize(28, 28)
            button.setIconSize(QSize(18, 18))
            button.setIcon(
                APP_THEME.icon(icon_names[player_id], color=APP_THEME.text_color)
            )
            button.setToolTip(f"Play with {player['label']}")
            button.setAccessibleName(f"Play with {player['label']}")
            self._style_player_button(button)
            button.clicked.connect(
                lambda checked=False, selected_player=player_id: (
                    self.video_player_requested.emit(selected_player)
                )
            )
            self._player_buttons[player_id] = button
            self.actions_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignRight)

        self.actions_widget.setFixedWidth(
            self.help_icon.width()
            + self.play_video_button.width()
            + len(self._player_buttons) * 28
            + 24
        )

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
        for button in self._player_buttons.values():
            self._style_player_button(button)

    @staticmethod
    def _style_player_button(button: QToolButton) -> None:
        button.setStyleSheet(APP_THEME.toggle_button_qss(button.objectName()))

    def _apply_title_style(self) -> None:
        self.title_label.setStyleSheet(APP_THEME.title_label_qss())
        self.title_label.ensurePolished()
        self.title_label.setContentsMargins(0, 4, 0, 8)
        self.title_label.setMinimumHeight(self.title_label.fontMetrics().height() + 16)
