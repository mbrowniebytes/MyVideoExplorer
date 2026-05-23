import pytest
from src.utils.str_util import StrUtil


class TestStrUtil:
    @pytest.fixture
    def str_util(self):
        return StrUtil()

    def test_join_strings(self, str_util):
        assert str_util.join_strings(["a", "b", "c"]) == "a, b, c"
        assert str_util.join_strings(["a"]) == "a"
        assert str_util.join_strings([]) == ""
        assert str_util.join_strings([1, 2, 3]) == "1, 2, 3"

    def test_elide_text(self):
        # This requires QFontMetrics, so it might need a QApp
        pass
