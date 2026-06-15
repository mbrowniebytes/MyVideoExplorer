import pytest
from unittest.mock import MagicMock, patch
from src.app.app_signals_model import SignalPayload, SignalFlow
from src.folder_nav.folder_nav import FolderNav
from src.folder_filter.folder_filter import FolderFilters
from src.settings.settings import Settings
from src.folder_filter.folder_filter_filter import FolderFilterFilter
from src.utils.file_util import FileUtil


class TestFolderNav:
    @pytest.fixture
    def folder_nav(self, qtbot):
        # Create real widgets to satisfy PySide6's type checking in layout.addWidget
        # but keep them minimal or stub their logic if needed
        settings = MagicMock(spec=Settings)
        settings.folder_configs = []
        settings.saved_filters = {}
        settings.settings_data_model = MagicMock()
        settings.sig_changed = MagicMock()

        file_util = MagicMock(spec=FileUtil)
        engine = MagicMock(spec=FolderFilterFilter)
        mock_log = MagicMock()
        filters = FolderFilters(engine, file_util, settings, mock_log)

        widget = FolderNav(filters, mock_log)

        widget.build()
        qtbot.addWidget(widget)
        return widget

    def test_ui_initialization(self, folder_nav):
        """Verify sub-widgets are added to layout."""
        # It has FolderNavFilters and a stretch
        assert folder_nav.layout().count() >= 1
        assert folder_nav.folder_filter_widget.parent() == folder_nav

    def test_set_root_folder(self, folder_nav):
        """Verify root folder is propagated to sub-widgets."""
        test_paths = ["/new/root"]
        folder_nav.set_root_folder(test_paths)
        assert folder_nav.root_folders == test_paths
        assert folder_nav.folder_filter_widget.root_folders == test_paths

    def test_apply_filters_call(self, folder_nav, qtbot):
        """Verify apply_filters propagates items from sub-widget."""
        mock_items = [MagicMock()]
        # Patch the real sub-widget's method
        with patch.object(
            folder_nav.folder_filter_widget, "apply_filters", return_value=mock_items
        ) as mock_apply:

            with qtbot.waitSignal(folder_nav.sig_selected_items) as blocker:
                folder_nav.apply_filters()

            mock_apply.assert_called()
            assert blocker.args[0].data == mock_items

    def test_signal_forwarding(self, folder_nav, qtbot):
        """Verify signals from sub-widgets are forwarded."""
        # Test sig_root_folder forwarding (emitted by filters when folder is selected from combo)
        with qtbot.waitSignal(folder_nav.sig_root_folder) as blocker:
            payload = SignalPayload(
                data="/emitted/path",
                sender="Test",
                name="Test",
                description="Test",
                flow=SignalFlow.USER_INPUT,
            )
            folder_nav.folder_filter_widget.sig_root_folder.emit(payload)
        assert blocker.args[0].data == "/emitted/path"

        # Test sig_genre_changed forwarding
        with qtbot.waitSignal(folder_nav.sig_genre_changed) as blocker:
            payload = SignalPayload(
                data="Action",
                sender="Test",
                name="Test",
                description="Test",
                flow=SignalFlow.USER_INPUT,
            )
            folder_nav.folder_filter_widget.sig_genre_changed.emit(payload)
        assert blocker.args[0].data == "Action"

    def test_apply_theme(self, folder_nav):
        """Verify theme application calls sub-widgets."""
        with patch.object(
            folder_nav.folder_filter_widget, "apply_theme"
        ) as mock_filter_theme:
            folder_nav.apply_theme()
            mock_filter_theme.assert_called_once()
