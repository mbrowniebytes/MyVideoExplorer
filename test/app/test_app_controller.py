import pytest
from unittest.mock import MagicMock
from MyVideoExplorer.app.app_controller import AppController
from MyVideoExplorer.app.app_state import AppState
from MyVideoExplorer.app.app_signals import SignalRegistry
from MyVideoExplorer.app.app_signals_model import SignalPayload


class TestAppController:
    @pytest.fixture
    def controller(self):
        mock_log = MagicMock()
        signals = SignalRegistry()
        return AppController(mock_log, signals)

    def test_initialization(self, controller):
        assert isinstance(controller.state, AppState)
        assert controller.state.root_folder == ""

    def test_set_root_folders(self, controller, qtbot):
        with qtbot.waitSignal(controller.signals.sig_root_folders) as blocker:
            controller.set_root_folders(["/root"])

        assert controller.state.root_folder == "/root"
        assert controller.state.current_folder == "/root"
        assert isinstance(blocker.args[0], SignalPayload)
        assert blocker.args[0].data == ["/root"]

    def test_set_current_file(self, controller, qtbot):
        with qtbot.waitSignal(controller.signals.sig_file_changed) as blocker:
            controller.set_current_file("/file.txt")

        assert controller.state.current_file == "/file.txt"
        assert isinstance(blocker.args[0], SignalPayload)
        assert blocker.args[0].data == "/file.txt"

    def test_set_current_tab(self, controller, qtbot):
        with qtbot.waitSignal(controller.signals.sig_tab_changed) as blocker:
            controller.set_current_tab(2)

        assert controller.state.current_tab == 2
        assert isinstance(blocker.args[0], SignalPayload)
        assert blocker.args[0].data == 2

    def test_selection_changed_emitted(self, controller, qtbot):
        with qtbot.waitSignal(controller.signals.sig_image_changed):
            controller.set_current_image("/img.jpg")
