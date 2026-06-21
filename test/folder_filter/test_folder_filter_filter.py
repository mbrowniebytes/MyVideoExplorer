import pytest
from unittest.mock import MagicMock
from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class TestFolderNavFiltersFilter:
    @pytest.fixture
    def filter_instance(self):
        nfo_util = MagicMock(spec=NfoParseUtil)
        instance = FolderFilterFilter(nfo_util)
        return instance

    def test_default_folders(self, filter_instance):
        """Verify that _default_folders returns only directories and dedupes them."""
        items = [
            FileUtilModel(type="dir", name="Dir1", full_path="/path/1", depth=0),
            FileUtilModel(type="dir", name="Dir1", full_path="/path/1", depth=0),
            FileUtilModel(type="file", name="File1", full_path="/path/f1", depth=0),
            FileUtilModel(type="dir", name="Dir2", full_path="/path/2", depth=0),
        ]
        result = filter_instance._default_folders(items)
        assert len(result) == 2
        assert result[0].name == "Dir1"
        assert result[1].name == "Dir2"

    def test_apply_filters_empty(self, filter_instance):
        """Verify apply_filters returns default folders when no filters are provided."""
        items = [
            FileUtilModel(type="dir", name="Dir1", full_path="/path/1", depth=0),
            FileUtilModel(type="file", name="File1", full_path="/path/f1", depth=0),
        ]
        result = filter_instance.apply_filters(items, [])
        assert len(result) == 1
        assert result[0].name == "Dir1"

    def test_apply_filters_with_folder_match(self, filter_instance):
        """Verify filtering by folder name."""
        items = [
            FileUtilModel(
                type="dir", name="Movie Alpha", full_path="/path/alpha", depth=0
            ),
            FileUtilModel(
                type="dir", name="Series Beta", full_path="/path/beta", depth=0
            ),
        ]
        filters = [{"filter": "folder", "value": "Alpha"}]
        result = filter_instance.apply_filters(items, filters)
        assert len(result) == 1
        assert result[0].name == "Movie Alpha"

    def test_apply_filters_with_file_match(self, filter_instance):
        """Verify filtering by file name inside folder."""
        items = [
            FileUtilModel(type="dir", name="Folder1", full_path="/path/1", depth=0),
            FileUtilModel(
                type="file",
                name="video_match.mp4",
                full_path="/path/1/video_match.mp4",
                depth=1,
            ),
            FileUtilModel(type="dir", name="Folder2", full_path="/path/2", depth=0),
            FileUtilModel(
                type="file", name="other.mp4", full_path="/path/2/other.mp4", depth=1
            ),
        ]
        filters = [{"filter": "file", "value": "match"}]
        result = filter_instance.apply_filters(items, filters)
        assert len(result) == 1
        assert result[0].name == "Folder1"

    def test_apply_filters_with_nfo_genre_match(self, filter_instance):
        """Verify filtering by genre from NFO file."""
        items = [
            FileUtilModel(
                type="dir", name="Sci-Fi Movie", full_path="/path/scifi", depth=0
            ),
            FileUtilModel(
                type="file",
                name="movie.nfo",
                full_path="/path/scifi/movie.nfo",
                depth=1,
                file_type="nfo",
            ),
        ]
        filter_instance.nfo_parse_util.parse_nfo.return_value = {
            "genres": ["Action", "Sci-Fi"]
        }

        # Test with filter list - using lowercase for match
        filters = [{"filter": "genre", "value": "sci-fi"}]
        result = filter_instance.apply_filters(items, filters)
        assert len(result) == 1
        assert result[0].name == "Sci-Fi Movie"

    def test_item_matches_actor(self, filter_instance):
        """Test NFO actor matching."""
        item = FileUtilModel(
            type="file",
            name="movie.nfo",
            full_path="/path/nfo",
            depth=1,
            file_type="nfo",
        )
        filter_instance.nfo_parse_util.parse_nfo.return_value = {
            "actors": ["Tom Cruise", "Brad Pitt"]
        }
        filters = [{"filter": "actor", "value": "cruise"}]
        assert filter_instance._item_matches(item, filters) is True

    def test_item_matches_director(self, filter_instance):
        """Test NFO director matching."""
        item = FileUtilModel(
            type="file",
            name="movie.nfo",
            full_path="/path/nfo",
            depth=1,
            file_type="nfo",
        )
        filter_instance.nfo_parse_util.parse_nfo.return_value = {
            "director": "Steven Spielberg"
        }
        filters = [{"filter": "director", "value": "spielberg"}]
        assert filter_instance._item_matches(item, filters) is True
