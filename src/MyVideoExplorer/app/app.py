from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
)

from MyVideoExplorer.app.app_builder import AppBuilder
from MyVideoExplorer.app.app_container import AppContainer
from MyVideoExplorer.app.app_state_handler import AppStateHandler


class App:
    def __init__(
        self,
        app: QApplication,
        container: AppContainer,
        window: QMainWindow,
    ) -> None:
        self.app = app
        self.window = window
        self.container = container
        self.builder = AppBuilder(container, app, window)
        self.state_handler = AppStateHandler(container, window)

    def build(self) -> QWidget:
        return self.builder.build()

    def initialize(self) -> None:
        self.state_handler.initialize()

    def close(self) -> None:
        self.state_handler.close()
