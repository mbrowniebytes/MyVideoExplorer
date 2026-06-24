from PySide6.QtWidgets import QApplication, QTabWidget, QComboBox
from MyVideoExplorer.app.app import App
from MyVideoExplorer.app.app_container import AppContainer
from MyVideoExplorer.theme.theme import APP_THEME

class TestThemeOnLoad:
    def test_theme_applied_after_build(self, qtbot):
        # We need to mock or use a real AppContainer
        # Since AppContainer initializes a lot of things, let's try to use it if possible
        # or mock the minimal parts.
        container = AppContainer()

        # Ensure we have a clean state
        APP_THEME.app = QApplication.instance()

        app = App(APP_THEME.app, container)
        window = app.build()
        qtbot.addWidget(window)

        # Find Settings widget
        from MyVideoExplorer.settings.settings import Settings
        settings = window.findChild(Settings)
        assert settings is not None

        # Check QTabWidget in settings
        tabs = settings.findChild(QTabWidget)
        assert tabs is not None

        # Verify stylesheet contains theme colors/styles
        # APP_THEME.tabs_qss() should be in the stylesheet
        assert APP_THEME.config.color_surface_primary in tabs.styleSheet()

        # Check QComboBox in SettingsAppTab
        from MyVideoExplorer.settings.settings_app_tab import SettingsAppTab
        app_tab = settings.findChild(SettingsAppTab)
        assert app_tab is not None
        combo = app_tab.findChild(QComboBox)
        assert combo is not None

        # Verify combo box stylesheet
        assert APP_THEME.config.color_surface_primary in combo.styleSheet()

        # Check Font
        assert combo.font().pointSize() == APP_THEME.font_size or combo.font().pixelSize() == APP_THEME.font_size
