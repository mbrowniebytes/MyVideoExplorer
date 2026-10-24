from unittest.mock import MagicMock

from MyVideoExplorer.settings.settings_app_tab import SettingsAppTab


def test_scan_media_timeout_options_update_and_save_state(qtbot):
    state = MagicMock()
    state.scan_media_timeout_seconds = 120
    tab = SettingsAppTab(state, MagicMock())
    qtbot.addWidget(tab)

    assert [
        tab.scan_media_timeout_combo.itemText(index)
        for index in range(tab.scan_media_timeout_combo.count())
    ] == ["30s", "60s", "120s", "300s"]

    tab.scan_media_timeout_combo.setCurrentIndex(
        tab.scan_media_timeout_combo.findData(300)
    )
    assert state.scan_media_timeout_seconds == 300

    tab._save_app_settings()
    state.save_app.assert_called_once_with()
    assert state.scan_media_timeout_seconds == 300


def test_scan_media_timeout_defaults_when_unsupported(qtbot):
    state = MagicMock()
    state.scan_media_timeout_seconds = 45
    tab = SettingsAppTab(state, MagicMock())
    qtbot.addWidget(tab)

    assert tab.scan_media_timeout_combo.currentData() == 120
