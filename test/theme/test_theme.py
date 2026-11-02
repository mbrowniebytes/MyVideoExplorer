import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QListWidget,
    QPushButton,
    QRadioButton,
    QTabBar,
    QToolButton,
)

from MyVideoExplorer.theme.theme import Theme


class TestTheme:
    @pytest.fixture
    def theme(self):
        return Theme()

    def test_initialization(self, theme):
        assert "Lato" in theme.font_family
        assert theme.font_size == 18
        assert theme.icon_size == 20

    def test_app_qss(self, theme):
        qss = theme.app_qss()
        assert "background: #111111" in qss
        assert "QToolTip" in qss
        # QWidget font size is handled via setFont, not QSS
        assert f"font-family: {theme.font_family}" in qss

    def test_button_qss(self, theme):
        qss = theme.button_qss()
        assert "QAbstractButton" in qss
        # Buttons use surface_color
        assert theme.surface_color in qss

    def test_setup_list_widget(self, theme, qtbot):
        lw = QListWidget()
        qtbot.addWidget(lw)
        theme.setup_list_widget(lw)

        # Verify icon size is set
        assert lw.iconSize() == QSize(theme.icon_size, theme.icon_size)
        assert lw.styleSheet() != ""

    def test_setup_interactive_widgets_uses_pointing_hand_cursor(self, theme, qtbot):
        widgets = [
            (QPushButton(), theme.setup_button),
            (QRadioButton(), theme.setup_button),
            (QCheckBox(), theme.setup_checkbox),
            (QTabBar(), theme.setup_tabs),
        ]
        for widget, setup in widgets:
            qtbot.addWidget(widget)
            setup(widget)
            assert widget.cursor().shape() == Qt.CursorShape.PointingHandCursor

    @pytest.mark.parametrize("object_name", ["meta_column_toggle", "nfo_column_toggle"])
    def test_setup_toggle_button_preserves_borderless_style(
        self, theme, qtbot, object_name
    ):
        button = QToolButton()
        button.setObjectName(object_name)
        qtbot.addWidget(button)

        theme.setup_button(button)

        assert "border: none" in button.styleSheet()
        assert "border: 2px solid" not in button.styleSheet()

    def test_refresh_theme(self, theme, qtbot):
        import sys
        from typing import cast

        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

        qapp = cast(QApplication, QApplication.instance() or QApplication(sys.argv))
        theme.app = qapp

        # Use QMainWindow as root, as it is a common root in real app
        window = QMainWindow()
        label = QLabel("Test", window)
        qtbot.addWidget(window)

        theme.font_size = 20
        theme.refresh_theme()  # Refresh entire app

        # QApplication stylesheet should be updated (background etc)
        assert "background: #111111" in qapp.styleSheet()

        # Label should have the font set via recursive refresh
        assert label.font().pixelSize() == 20

    def test_safe_icon(self, theme):
        from PySide6.QtGui import QIcon

        # Test valid icon
        icon = theme.icon("fa6s.folder")
        assert isinstance(icon, QIcon)
        assert not icon.isNull()

        # Test invalid icon - should not raise exception and return a valid icon
        icon_invalid = theme.icon("invalid.icon.name")
        assert isinstance(icon_invalid, QIcon)
        assert not icon_invalid.isNull()
