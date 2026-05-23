import pytest
from PySide6.QtWidgets import QHeaderView
from src.widgets.simple_table_widget import SimpleTableWidget


class TestSimpleTable:
    @pytest.fixture
    def sample_data(self):
        rows = [
            {"col1": "val1a", "col2": "val2a"},
            {"col1": "val1b", "col2": "val2b"},
        ]
        cols = ["col1", "col2"]
        headers = ["Header 1", "Header 2"]
        resize_modes = [
            QHeaderView.ResizeMode.Stretch,
            QHeaderView.ResizeMode.ResizeToContents,
        ]
        return rows, cols, headers, resize_modes

    @pytest.fixture
    def simple_table(self, qtbot, sample_data):
        rows, cols, headers, resize_modes = sample_data
        table = SimpleTableWidget(rows, cols, headers, resize_modes)
        qtbot.addWidget(table)
        return table

    def test_initialization(self, simple_table):
        assert simple_table.table is not None
        assert simple_table.model is not None
        assert simple_table.model.rowCount() == 2
        assert simple_table.model.columnCount() == 2

    def test_update_rows(self, simple_table):
        new_rows = [{"col1": "new1", "col2": "new2"}]
        simple_table.update_rows(new_rows)
        assert simple_table.model.rowCount() == 1
        assert simple_table.model.data(simple_table.model.index(0, 0)) == "new1"

    def test_apply_theme(self, simple_table):
        simple_table.apply_theme()
        assert simple_table.table.font().pointSize() > 0
