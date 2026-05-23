import pytest
from unittest.mock import MagicMock
from xml.etree import ElementTree
from src.utils.nfo_parse_util import NfoParseUtil
from src.utils.file_util import FileUtil


class TestNfoParseUtil:
    @pytest.fixture
    def nfo_util(self):
        file_util = MagicMock(spec=FileUtil)
        return NfoParseUtil(file_util)

    def test_create_empty_movie_info(self, nfo_util):
        info = nfo_util.create_empty_movie_info()
        assert info["title"] == ""
        assert isinstance(info["genres"], list)
        assert isinstance(info["actors"], list)

    def test_parse_basic_fields(self, nfo_util):
        xml_data = """
        <movie>
            <title>Test Movie</title>
            <year>2024</year>
            <plot>Test plot.</plot>
        </movie>
        """
        root = ElementTree.fromstring(xml_data)
        info = nfo_util.create_empty_movie_info()
        nfo_util._parse_basic_fields(root, info)
        assert info["title"] == "Test Movie"
        assert info["year"] == 2024
        assert info["plot"] == "Test plot."

    def test_parse_genres(self, nfo_util):
        xml_data = """
        <movie>
            <genre>Action</genre>
            <genre>Sci-Fi</genre>
        </movie>
        """
        root = ElementTree.fromstring(xml_data)
        info = nfo_util.create_empty_movie_info()
        nfo_util._parse_genres(root, info)
        assert "Action" in info["genres"]
        assert "Sci-Fi" in info["genres"]

    def test_to_int(self, nfo_util):
        assert nfo_util._to_int("123") == 123
        assert nfo_util._to_int("abc") == 0
        assert nfo_util._to_int(None) == 0

    def test_clean_text(self, nfo_util):
        assert nfo_util._clean_text("  hello  ") == "hello"
        assert nfo_util._clean_text(None) == ""

    def test_caching(self, nfo_util):
        folder_path = "test_folder"
        nfo_file = "test_folder/movie.nfo"
        nfo_util.file_util.find_nfo_file.return_value = nfo_file

        # Mock parse_nfo_file to avoid actual file operations
        mock_info = {"title": "Cached Movie"}
        nfo_util.parse_nfo_file = MagicMock(return_value=mock_info)

        # First call should call find_nfo_file and parse_nfo_file
        res1 = nfo_util.parse_nfo_folder(folder_path)
        assert res1 == mock_info
        assert nfo_util.file_util.find_nfo_file.call_count == 1
        assert nfo_util.parse_nfo_file.call_count == 1

        # Second call with same folder should use cache
        res2 = nfo_util.parse_nfo_folder(folder_path)
        assert res2 == mock_info
        assert nfo_util.file_util.find_nfo_file.call_count == 1
        assert nfo_util.parse_nfo_file.call_count == 1

        # Call with different folder should refresh cache
        folder_path2 = "test_folder2"
        nfo_util.file_util.find_nfo_file.return_value = "test_folder2/movie.nfo"
        nfo_util.parse_nfo_folder(folder_path2)
        assert nfo_util.file_util.find_nfo_file.call_count == 2
        assert nfo_util.parse_nfo_file.call_count == 2
