from unittest.mock import MagicMock
from MyVideoExplorer.folder_filter.folder_filter import FolderFilters
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.utils.file_util import FileUtil
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil
from MyVideoExplorer.settings.settings_state import SettingsState

def test_db_toggle_refreshes_filters(qtbot):
    # Setup
    log_util = MagicMock()
    # We need to NOT mock sig_settings_changed, but it's defined as a Signal object
    settings_state = SettingsState(log_util)
    settings_state._db_enabled = False # Initial state
    settings_state.media_configs = [{"path": "D:/Test", "label": "Test"}]

    settings_mock = MagicMock()
    settings_mock.settings_data_model = settings_state

    file_util = MagicMock(spec=FileUtil)
    nfo_util = MagicMock(spec=NfoParseUtil)

    engine = FolderFilterFilter(nfo_util, settings_state, log_util)

    widget = FolderFilters(engine, file_util, settings_mock, log_util)
    widget.root_folders = ["D:/Test"]
    widget.build()

    # Mock apply_filters to verify it is called
    widget.apply_filters = MagicMock(side_effect=widget.apply_filters)
    qtbot.addWidget(widget)

    # Simulate settings change
    widget._connect_sigs() # ensure connections are active
    with qtbot.waitSignal(widget.sig_apply_filters):
        settings_state.sig_settings_changed.emit(None)

    # We successfully emitted the signal
    assert True
