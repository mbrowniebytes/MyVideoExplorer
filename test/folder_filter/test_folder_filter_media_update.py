from unittest.mock import MagicMock, patch
from src.settings.settings_state import SettingsState
from src.folder_filter.folder_filter_media import FolderFilterMedia

def test_refresh_on_signal(qtbot):
    mock_log_util = MagicMock()
    with patch("src.settings.settings_state.SettingsState._load_settings"):
        with patch("src.settings.settings_state.SettingsState._ensure_defaults"):
            state = SettingsState(mock_log_util)
            state.folder_configs = [{"label": "Media1", "path": "/path1"}]

            # Need a mock settings object that has settings_data_model
            settings = MagicMock()
            settings.settings_data_model = state

            folder_filter = FolderFilterMedia(settings)
            qtbot.addWidget(folder_filter)

            # Check initial button label
            assert folder_filter.media_button_group[0].text() == "Medi" # 4 chars

            # Update label
            state.folder_configs[0]["label"] = "NewMedia"

            # Emit signal - this is what SHOULD happen when saving settings
            state.sig_settings_changed.emit()

            # Check if button updated
            assert folder_filter.media_button_group[0].text() == "NewM"
