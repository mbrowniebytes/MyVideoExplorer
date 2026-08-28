from __future__ import annotations
import random
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QMainWindow, QApplication
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.lang.lang_loader import LangLoader


class AppLoadingWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        app_label = QLabel("MyVideoExplorer")
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_label.setStyleSheet(APP_THEME.loading_label_qss())
        layout.addWidget(app_label)

        path_to_icon = FileUtil.get_resource_path("asset/app.png")
        pixmap = QPixmap()
        pixmap.loadFromData(Path(path_to_icon).read_bytes())
        pixmap = pixmap.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        lang = LangLoader.get_lang("en")
        msg = random.choice(lang.messages)
        loading_label = QLabel(msg)
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setStyleSheet(APP_THEME.loading_label_qss())
        layout.addWidget(loading_label)

    def setup_window(self, window: QMainWindow, app: QApplication) -> None:
        window.setWindowTitle("MyVideoExplorer")
        path_to_icon = FileUtil.get_resource_path("asset/app.png")
        pixmap = QPixmap()
        pixmap.loadFromData(Path(path_to_icon).read_bytes())
        appIcon = QIcon(pixmap)
        app.setWindowIcon(appIcon)
