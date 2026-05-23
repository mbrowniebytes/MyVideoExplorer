from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout
from src.theme.theme import APP_THEME
from PySide6.QtGui import QFont


class ImageTitleWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(5)

        self.title_label = QLabel("")
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.title_label.setStyleSheet(APP_THEME.title_label_qss())

        self.help_icon = QLabel("?")
        self.help_icon.setFixedSize(20, 20)
        self.help_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.help_icon.setStyleSheet(APP_THEME.help_icon_label_qss())

        self.help_icon.setToolTip(
            "Image Preview Usage:\n"
            "- Use Mouse Wheel to scroll through folders\n"
            "- Double click on image to play media\n"
            "- Right click to scroll through images in current folder"
        )

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addWidget(self.help_icon)

    def update_title(self, title: str) -> None:
        if self.title_label.text() == title:
            return
        self.title_label.setText(title)

    def apply_theme(self) -> None:
        self.title_label.setStyleSheet(APP_THEME.title_label_qss())
        self.title_label.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size + 20))
        self.help_icon.setStyleSheet(
            APP_THEME.label_qss("small")
            + "; border: 1px solid palette(text); border-radius: 10px;"
        )
