from PySide6.QtGui import QFont
from PySide6.QtWidgets import QVBoxLayout, QWidget, QPushButton

from MyVideoExplorer.theme.theme import APP_THEME


class CollapsibleBoxWidget(QWidget):
    """A reusable collapsible box widget with a toggle button and content area."""

    def __init__(
        self,
        label: str = "",
        parent: QWidget | None = None,
        collapsed: bool = False,
    ) -> None:
        super().__init__(parent)

        # Eager initialization removes the need for redundant None checks later
        self.label = label
        self.toggle_button = QPushButton(self.label)
        self.content_area = QWidget(self)
        self.layout = QVBoxLayout(self)
        self.content_layout = QVBoxLayout()

        self.collapsed = collapsed

        self._setup_ui()
        self._apply_initial_state()

    def _setup_ui(self) -> None:
        """Configure layouts, widget properties, and signal connections."""
        # Toggle button configuration
        self.toggle_button.setCheckable(True)
        self.toggle_button.clicked.connect(self._toggle_content)

        # Main layout configuration
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.toggle_button)
        self.layout.addWidget(self.content_area)

        # Assign layout to content area immediately for consistent behavior
        self.content_area.setLayout(self.content_layout)

    def _apply_initial_state(self) -> None:
        """Apply initial collapsed state and default styling."""
        self._set_collapsed(self.collapsed)
        self.toggle_button.setStyleSheet(APP_THEME.button_qss())

    def _set_collapsed(self, collapsed: bool) -> None:
        """Synchronize UI elements with the collapsed state.

        Using a single method ensures button check-state and content visibility
        always remain in sync, preventing UI desync bugs.
        """
        self.collapsed = collapsed
        self.toggle_button.setChecked(not collapsed)
        self.content_area.setVisible(not collapsed)

    def _toggle_content(self) -> None:
        """Handle toggle button click by flipping the collapsed state."""
        self._set_collapsed(not self.collapsed)

    def add_widget(self, widget: QWidget) -> None:
        """Add a widget to the content area layout."""
        self.content_layout.addWidget(widget)

    def apply_theme(self) -> None:
        """Apply application theme fonts and styles to relevant widgets.

        Note: Applies styling only to direct children to avoid overriding
        nested widget styles or causing performance issues with findChildren().
        Global theming should ideally be handled at the QApplication level.
        """
        font = QFont(APP_THEME.font_family, APP_THEME.font_size)

        self.setFont(font)
        self.toggle_button.setFont(font)
        self.content_area.setFont(font)

        self.setStyleSheet(APP_THEME.container_qss())
