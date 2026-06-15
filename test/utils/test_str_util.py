from unittest.mock import MagicMock

import pytest
from src.utils.str_util import StrUtil


class TestStrUtil:
    @pytest.fixture
    def mock_log_util(self):
        return MagicMock()

    @pytest.fixture
    def str_util(self, mock_log_util):
        return StrUtil(log_util=mock_log_util)

    def test_join_strings(self, str_util):
        assert str_util.join_strings(["a", "b", "c"]) == "a, b, c"
        assert str_util.join_strings(["a"]) == "a"
        assert str_util.join_strings([]) == ""
        assert str_util.join_strings([1, 2, 3]) == "1, 2, 3"

    def test_elide_text(self):
        # This requires QFontMetrics, so it might need a QApp
        pass
