import pytest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QWheelEvent
from src.image_list.image_label import ImageLabel


class TestImageLabel:
    @pytest.fixture
    def image_label(self, qtbot):
        label = ImageLabel()
        qtbot.addWidget(label)
        return label

    def test_initialization(self, image_label):
        assert image_label.alignment() == Qt.AlignmentFlag.AlignCenter
        assert (
            image_label.sizePolicy().horizontalPolicy()
            == pytest.importorskip("PySide6.QtWidgets").QSizePolicy.Policy.Expanding
        )

    def test_wheel_event_emits_signal(self, image_label, qtbot):
        # Mocking wheel event
        with qtbot.waitSignal(image_label.sig_wheel_step) as blocker:
            # Positive delta (scroll up) -> step -1
            event = QWheelEvent(
                QPoint(0, 0),
                QPoint(0, 0),
                QPoint(0, 0),
                QPoint(0, 120),
                Qt.NoButton,
                Qt.NoModifier,
                Qt.ScrollPhase.NoScrollPhase,
                False,
            )
            image_label.wheelEvent(event)
        assert blocker.args[0] == -1

        with qtbot.waitSignal(image_label.sig_wheel_step) as blocker:
            # Negative delta (scroll down) -> step 1
            event = QWheelEvent(
                QPoint(0, 0),
                QPoint(0, 0),
                QPoint(0, 0),
                QPoint(0, -120),
                Qt.NoButton,
                Qt.NoModifier,
                Qt.ScrollPhase.NoScrollPhase,
                False,
            )
            image_label.wheelEvent(event)
        assert blocker.args[0] == 1

    def test_mouse_press_right_button_emits_signal(self, image_label, qtbot):
        with qtbot.waitSignal(image_label.sig_right_click) as blocker:
            qtbot.mousePress(image_label, Qt.RightButton)
        assert blocker.signal_triggered

    def test_mouse_double_click_emits_signal(self, image_label, qtbot):
        with qtbot.waitSignal(image_label.sig_double_click) as blocker:
            qtbot.mouseDClick(image_label, Qt.LeftButton)
        assert blocker.signal_triggered
