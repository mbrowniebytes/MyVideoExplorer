import pytest
from unittest.mock import MagicMock, patch
from MyVideoExplorer.settings.settings import Settings

def test_save_media_settings_calls_state_save_media(qtbot):
    mock_log_util = MagicMock()
    mock_file_util = MagicMock()
    
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch("MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"):
            # Mock save_media in SettingsState
            with patch("MyVideoExplorer.settings.settings_state.SettingsState.save_media") as mock_save:
                s = Settings(mock_log_util, mock_file_util)
                
                # Mock UI interaction to avoid segfaults/errors
                s.media_settings_tab.db_enabled_dropdown = MagicMock()
                s.media_settings_tab.db_enabled_dropdown.currentText.return_value = 'Yes'
                
                s.media_settings_tab._save_media_settings()
                
                mock_save.assert_called_once()
