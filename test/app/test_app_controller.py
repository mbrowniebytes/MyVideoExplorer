import pytest
from unittest.mock import MagicMock
from src.app.app_controller import AppController
from src.app.app_state import AppState


class TestAppController:
    @pytest.fixture
    def controller(self):
        mock_log = MagicMock()
        return AppController(mock_log)

    def test_initialization(self, controller):
        assert isinstance(controller.state, AppState)
        assert controller.state.root_folder == ""

    def test_set_root_folder(self, controller, qtbot):
        with qtbot.waitSignal(controller.sig_root_folders) as blocker:
            controller.set_root_folder(["/root"])

        assert controller.state.root_folder == "/root"
        assert controller.state.current_folder == "/root"
        assert blocker.args[0] == ["/root"]

    def test_set_current_file(self, controller, qtbot):
        with qtbot.waitSignal(controller.sig_file_changed) as blocker:
            controller.set_current_file("/file.txt")

        assert controller.state.current_file == "/file.txt"
        assert blocker.args[0] == "/file.txt"

    def test_set_current_tab(self, controller, qtbot):
        with qtbot.waitSignal(controller.sig_tab_changed) as blocker:
            controller.set_current_tab(2)

        assert controller.state.current_tab == 2
        assert blocker.args[0] == 2

    def test_selection_changed_emitted(self, controller, qtbot):
        with qtbot.waitSignal(controller.sig_image_changed):
            controller.set_current_image("/img.jpg")
