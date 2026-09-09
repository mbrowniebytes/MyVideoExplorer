import pytest
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget
from MyVideoExplorer.widgets.right_aligned_tab_bar import RightAlignedTabBar


@pytest.fixture
def app():
    app = QApplication.instance() or QApplication([])
    return app


def test_right_aligned_tab_bar(app):
    tab_widget = QTabWidget()
    tab_widget.resize(800, 600)  # Resize the tab widget
    tab_bar = RightAlignedTabBar(tab_widget)
    tab_widget.setTabBar(tab_bar)
    tab_widget.addTab(QWidget(), "Tab 1")
    tab_widget.addTab(QWidget(), "Tab 2")
    tab_widget.addTab(QWidget(), "Spacer")
    tab_widget.addTab(QWidget(), "Settings")

    # This should trigger tabSizeHint
    size = tab_bar.tabSizeHint(2)
    print(f"DEBUG: spacer size={size}")
