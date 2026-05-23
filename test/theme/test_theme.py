import pytest
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QListWidget, QWidget
from src.theme.theme import Theme


class TestTheme:
    @pytest.fixture
    def theme(self):
        return Theme()

    def test_initialization(self, theme):
        assert theme.font_family == "Segoe UI"
        assert theme.font_size == 18
        assert theme.icon_size == 20

    def test_app_qss(self, theme):
        qss = theme.app_qss()
        assert "background: #111111" in qss
        assert "QToolTip" in qss
        assert f"font-size: {theme.font_size}px" in qss

    def test_button_qss(self, theme):
        qss = theme.button_qss()
        assert "QAbstractButton" in qss
        # Buttons use surface_color
        assert theme.surface_color in qss

    def test_setup_list_widget(self, theme, qtbot):
        lw = QListWidget()
        qtbot.addWidget(lw)
        theme.setup_list_widget(lw)
        assert lw.font().family() == theme.font_family

    def test_refresh_theme(self, theme, qtbot):
        from PySide6.QtWidgets import QApplication, QLabel
        import sys

        qapp = QApplication.instance() or QApplication(sys.argv)
        theme.app = qapp

        widget = QWidget()
        label = QLabel("Test", widget)
        # Force Segoe UI font to match theme expectation
        label.setFont(QFont("Segoe UI", 18))
        qtbot.addWidget(widget)

        theme.font_size = 20
        # The current Theme._refresh_widget only handles specific classes
        # and doesn't recurse if the class matches.
        theme.refresh_theme(label)  # Refresh the label directly

        assert label.font().pointSize() == 20

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
