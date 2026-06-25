import pytest
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QListWidget

from MyVideoExplorer.theme.theme import Theme


class TestTheme:
    @pytest.fixture
    def theme(self):
        return Theme()

    def test_initialization(self, theme):
        assert "Segoe UI" in theme.font_family
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

    def test_refresh_theme(self, theme, qtbot):
        import sys

        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

        qapp = QApplication.instance() or QApplication(sys.argv)
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
        icon = theme.icon("fa5s.folder")
        assert isinstance(icon, QIcon)
        assert not icon.isNull()

        # Test invalid icon - should not raise exception and return a valid icon
        icon_invalid = theme.icon("invalid.icon.name")
        assert isinstance(icon_invalid, QIcon)
        assert not icon_invalid.isNull()
