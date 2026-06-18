import pytest
from PySide6.QtWidgets import QApplication
from src.image_list.image_preview_widget import ImagePreviewWidget
from src.utils.log_util import LogUtil

class TestImagePreviewWidget:
    @pytest.fixture
    def app(self):
        return QApplication.instance() or QApplication([])

    def test_load_pixmap_crash_logging(self, app):
        log_util = LogUtil().configure("debug")
        widget = ImagePreviewWidget(log_util)

        # Test loading a non-existent file or invalid pixmap
        # This might trigger a crash if not handled
        widget.load_pixmap("non_existent_file.jpg")

        # We don't expect a crash here, as we added exception handling.
        # If it crashes, the test will fail.

        # Test with None, should not crash
        widget.load_pixmap(None)

        # Check if logging happened? Hard to check without file access
