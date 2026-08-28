import pytest
from unittest.mock import MagicMock, patch
from MyVideoExplorer.app.app_signals_model import SignalPayload
from MyVideoExplorer.settings.settings_media_tab import SettingsMediaTab

class TestMediaSettingsSignals:
    @pytest.fixture
    def settings_media_tab(self, qtbot):
        mock_state = MagicMock()
        mock_log_util = MagicMock()
        mock_file_util = MagicMock()
        
        with patch.object(SettingsMediaTab, "_build_ui", return_value=None):
            
            tab = SettingsMediaTab(mock_state, mock_log_util, mock_file_util)
            tab.reset_save_button = MagicMock()
            
            # Setup mock dropdown
            tab.db_enabled_dropdown = MagicMock()
            tab.db_enabled_dropdown.currentText.return_value = 'Yes'
            
            qtbot.addWidget(tab)
            return tab

    def test_save_media_settings_emits_settings_changed(self, settings_media_tab):
        """Verify that _save_media_settings emits settings_changed signal on state."""
        
        # When save_media_settings is called, it should call state.sig_settings_changed.emit
        settings_media_tab._save_media_settings()
        
        # Check if sig_settings_changed was emitted
        assert settings_media_tab.state.sig_settings_changed.emit.called
        
        # Verify the payload
        args = settings_media_tab.state.sig_settings_changed.emit.call_args[0][0]
        assert isinstance(args, SignalPayload)
        assert args.name == "Media Settings Saved"
