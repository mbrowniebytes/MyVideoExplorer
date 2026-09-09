from unittest.mock import MagicMock, patch

from MyVideoExplorer.folder_filter.folder_filter_media import FolderFilterMedia
from MyVideoExplorer.settings.settings_state import SettingsState


def test_refresh_on_signal(qtbot):
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util)
            state.media_configs = [{"label": "Media1", "path": "/path1"}]

            # Need a mock settings object that has settings_data_model
            settings = MagicMock()
            settings.settings_data_model = state

            folder_filter = FolderFilterMedia(settings, mock_log_util)
            qtbot.addWidget(folder_filter)

            # Check initial button label
            assert folder_filter.media_button_group[0].text() == "Medi"  # 4 chars

            # Update label
            state.media_configs[0]["label"] = "NewMedia"

            from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload

            # Emit signal - this is what SHOULD happen when saving settings
            state.settings_changed.emit(
                SignalPayload(
                    data=None,
                    sender="Test",
                    name="Settings Changed",
                    description="Settings changed.",
                    flow=SignalFlow.COMPONENT_INTERACTION,
                )
            )

            # Check if button updated
            assert folder_filter.media_button_group[0].text() == "NewM"
