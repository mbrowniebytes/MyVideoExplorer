import pytest
from PySide6.QtCore import QSize
from MyVideoExplorer.widgets.label_angled_widget import LabelAngledWidget


class TestLabelAngled:
    @pytest.fixture
    def label_angled(self, qtbot):
        label = LabelAngledWidget("Test", angle=90)
        qtbot.addWidget(label)
        return label

    def test_initialization(self, label_angled):
        assert label_angled.text() == "Test"
        assert label_angled.angle == 90

    def test_size_hint(self, label_angled):
        hint = label_angled.sizeHint()
        assert isinstance(hint, QSize)
        assert hint.width() > 0
        assert hint.height() > 0

    def test_apply_theme(self, label_angled):
        label_angled.apply_theme()
        assert label_angled.font().family() != ""
