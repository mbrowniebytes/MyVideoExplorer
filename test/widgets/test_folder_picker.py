import pytest
from unittest.mock import patch
from src.widgets.folder_picker_widget import FolderPickerWidget as FolderPicker


class TestFolderPicker:
    @pytest.fixture
    def folder_picker(self, qtbot):
        picker = FolderPicker()
        qtbot.addWidget(picker)
        return picker

    def test_initialization(self, folder_picker):
        assert folder_picker.selected_folder == ""

    def test_selected_folder_setter_emits_signal(self, folder_picker, qtbot):
        with qtbot.waitSignal(folder_picker.sig_selected_folder) as blocker:
            folder_picker.selected_folder = "/new/path"
        assert folder_picker.selected_folder == "/new/path"
        assert blocker.args[0] == "/new/path"

    def test_selected_folder_setter_no_duplicates(self, folder_picker, qtbot):
        folder_picker.selected_folder = "/path"
        with qtbot.assertNotEmitted(folder_picker.sig_selected_folder):
            folder_picker.selected_folder = "/path"

    def test_select_folder_dialog(self, folder_picker, qtbot):
        with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory") as mock_dialog:
            mock_dialog.return_value = "/selected/path"
            folder_picker.select_folder()
            assert folder_picker.selected_folder == "/selected/path"

    def test_select_folder_cancelled(self, folder_picker, qtbot):
        folder_picker.selected_folder = "/initial"
        with patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory") as mock_dialog:
            mock_dialog.return_value = ""
            folder_picker.select_folder()
            assert folder_picker.selected_folder == "/initial"
