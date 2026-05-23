from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout, QWidget, QPushButton

from src.theme.theme import APP_THEME


class CollapsibleBoxWidget(QWidget):
    def __init__(
        self,
        label: str = "",
        parent: QWidget | None = None,
        collapsed: bool = False,
    ) -> None:
        super().__init__(parent)
        self.layout: QVBoxLayout | None = None
        self.content_area: QWidget | None = None
        self.toggle_button: QPushButton | None = None
        self.label = label
        self.collapsed = collapsed

        self.build()

    def build(self) -> None:
        self._build_toggle_button()
        self._build_content_area()
        self._build_layout()
        self._apply_style()
        self._apply_collapsed_state()

    def _build_toggle_button(self) -> None:
        self.toggle_button = QPushButton(self.label, self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self._toggle_content)

    def _build_content_area(self) -> None:
        self.content_area = QWidget(self)

    def _build_layout(self) -> None:
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        if self.toggle_button is not None:
            self.layout.addWidget(self.toggle_button)

        if self.content_area is not None:
            self.layout.addWidget(self.content_area)

    def _apply_style(self) -> None:
        if self.toggle_button is not None:
            self.toggle_button.setStyleSheet(APP_THEME.button_qss())

    def _apply_collapsed_state(self) -> None:
        if self.toggle_button is not None:
            self.toggle_button.setChecked(not self.collapsed)

        if self.content_area is not None:
            self.content_area.setVisible(not self.collapsed)

    def _toggle_content(self) -> None:
        if self.content_area is None:
            return
        visible = not self.content_area.isVisible()
        self.content_area.setVisible(visible)

    def add_widget(self, widget: QWidget) -> None:
        """Convenience method to add widgets to content area."""
        if self.content_area is None:
            return

        if self.content_area.layout() is None:
            self.content_area.setLayout(QVBoxLayout())

        layout = self.content_area.layout()
        if layout is not None:
            layout.addWidget(widget)

    def apply_theme(self) -> None:
        self.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
        self.setStyleSheet(APP_THEME.container_qss())

        for child in self.findChildren(QWidget):
            child.setFont(QFont(APP_THEME.font_family, APP_THEME.font_size))
