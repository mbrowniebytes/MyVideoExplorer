import pytest
from unittest.mock import MagicMock, patch
from MyVideoExplorer.settings.settings_media_tab import SettingsMediaTab
from MyVideoExplorer.settings.settings_state import SettingsState

class TestMediaSettingsDelayedEmit:
    @pytest.fixture
    def settings_media_tab(self, qtbot):
        mock_state = MagicMock(spec=SettingsState)
        mock_state.media_configs = [{"label": "test", "path": "D:/test", "icon": "fa5s.folder", "media_type": "movie"}]
        mock_state.db_enabled.return_value = True
        
        mock_log_util = MagicMock()
        mock_file_util = MagicMock()
        
        with patch.object(SettingsMediaTab, "_build_ui", return_value=None):
            tab = SettingsMediaTab(mock_state, mock_log_util, mock_file_util)
            
            tab.folder_nav_layout = MagicMock()
            tab.folder_nav_content = MagicMock()
            tab.db_enabled_dropdown = MagicMock()
            
            qtbot.addWidget(tab)
            return tab

    def test_premature_root_folders_changed_emit(self, settings_media_tab):
        """Verify that sig_root_folders_changed is NOT emitted on config change before save."""
        
        mock_callback = MagicMock()
        settings_media_tab.sig_root_folders_changed.connect(mock_callback)
        
        # Simulate a config change
        folder_config = settings_media_tab.state.media_configs[0]
        settings_media_tab._on_config_changed(folder_config, "path", "D:/new_test_path")
        
        # Assert NOT called
        assert not mock_callback.called
        
    def test_save_emits_root_folders_changed(self, settings_media_tab):
        """Verify that sig_root_folders_changed IS emitted on save."""
        
        mock_callback = MagicMock()
        settings_media_tab.sig_root_folders_changed.connect(mock_callback)
        
        # Now simulate save
        settings_media_tab._save_media_settings()
        
        # Assert called
        assert mock_callback.called
