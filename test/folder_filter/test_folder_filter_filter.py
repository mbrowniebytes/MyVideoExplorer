from unittest.mock import MagicMock

import pytest

from MyVideoExplorer.folder_filter.folder_filter_filter import FolderFilterFilter
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.utils.file_util_model import FileUtilModel
from MyVideoExplorer.utils.nfo_parse_util import NfoParseUtil


class TestFolderNavFiltersFilter:
    @pytest.fixture
    def filter_instance(self):
        nfo_util = MagicMock(spec=NfoParseUtil)
        settings_state = MagicMock(spec=SettingsState)
        settings_state.db_enabled.return_value = False
        instance = FolderFilterFilter(nfo_util, settings_state)
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
        """Verify apply_filters_requested returns default folders when no filters are provided."""
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

    def test_apply_filters_with_tag_match(self, filter_instance):
        """Verify filtering by tag."""
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
            "tags": ["Favorite", "4K HDR"]
        }

        filters = [{"filter": "Tag", "value": "Favorite"}]
        result = filter_instance.apply_filters(items, filters)
        assert len(result) == 1
        assert result[0].name == "Sci-Fi Movie"

        # Multi-tag comma-separated filter value
        filters_multi = [{"filter": "Tag", "value": "Classic, 4K HDR"}]
        result_multi = filter_instance.apply_filters(items, filters_multi)
        assert len(result_multi) == 1
        assert result_multi[0].name == "Sci-Fi Movie"

        # Non-matching multi-tag filter
        filters_none = [{"filter": "Tag", "value": "Horror, Comedy"}]
        result_none = filter_instance.apply_filters(items, filters_none)
        assert len(result_none) == 0

    def test_item_matches_title(self, filter_instance):
        """Test NFO title matching."""
        item = FileUtilModel(
            type="file",
            name="movie.nfo",
            full_path="/path/nfo",
            depth=1,
            file_type="nfo",
        )
        filter_instance.nfo_parse_util.parse_nfo.return_value = {
            "title": "Inception",
            "plot": "A thief who steals corporate secrets through dream-sharing technology",
        }
        assert (
            filter_instance._item_matches(
                item, [{"filter": "title", "value": "Inception"}]
            )
            is True
        )
        assert (
            filter_instance._item_matches(
                item, [{"filter": "title", "value": "Avatar"}]
            )
            is False
        )

    def test_apply_filters_dirs_first_hierarchy(self, filter_instance):
        """Verify filtering when all directory items precede all file items in input list."""
        items = [
            FileUtilModel(
                type="dir",
                name="The Matrix (1999)",
                full_path="/movies/matrix",
                depth=1,
            ),
            FileUtilModel(
                type="dir", name="Titanic (1997)", full_path="/movies/titanic", depth=1
            ),
            FileUtilModel(
                type="file",
                name="matrix.mkv",
                full_path="/movies/matrix/matrix.mkv",
                depth=2,
                file_type="video",
            ),
            FileUtilModel(
                type="file",
                name="movie.nfo",
                full_path="/movies/matrix/movie.nfo",
                depth=2,
                file_type="nfo",
            ),
            FileUtilModel(
                type="file",
                name="titanic.mkv",
                full_path="/movies/titanic/titanic.mkv",
                depth=2,
                file_type="video",
            ),
            FileUtilModel(
                type="file",
                name="movie.nfo",
                full_path="/movies/titanic/movie.nfo",
                depth=2,
                file_type="nfo",
            ),
        ]

        def parse_nfo_mock(nfo_file):
            if "matrix" in nfo_file:
                return {
                    "title": "The Matrix",
                    "genres": ["Action", "Sci-Fi"],
                    "tags": ["Cyberpunk", "Favorite"],
                }
            return {
                "title": "Titanic",
                "genres": ["Drama", "Romance"],
                "tags": ["Classic"],
            }

        filter_instance.nfo_parse_util.parse_nfo.side_effect = parse_nfo_mock

        # Filter by Sci-Fi genre: only Matrix should match
        result = filter_instance.apply_filters(
            items, [{"filter": "Genre", "value": "Sci-Fi"}]
        )
        assert len(result) == 1
        assert result[0].name == "The Matrix (1999)"
        assert result[0].full_path == "/movies/matrix"

        # Filter by Drama genre: only Titanic should match
        result = filter_instance.apply_filters(
            items, [{"filter": "Genre", "value": "Drama"}]
        )
        assert len(result) == 1
        assert result[0].name == "Titanic (1997)"
        assert result[0].full_path == "/movies/titanic"

        # Combined filter: Folder 'Matrix' AND Genre 'Action'
        result = filter_instance.apply_filters(
            items,
            [
                {"filter": "Folder", "value": "Matrix"},
                {"filter": "Genre", "value": "Action"},
            ],
        )
        assert len(result) == 1
        assert result[0].name == "The Matrix (1999)"

        # Combined filter: Folder 'Titanic' AND Genre 'Sci-Fi' -> no match
        result = filter_instance.apply_filters(
            items,
            [
                {"filter": "Folder", "value": "Titanic"},
                {"filter": "Genre", "value": "Sci-Fi"},
            ],
        )
        assert len(result) == 0

    def test_apply_filters_nfo_filter(self, filter_instance):
        """Verify filtering with generic NFO filter type."""
        items = [
            FileUtilModel(type="dir", name="Movie 1", full_path="/movies/m1", depth=1),
            FileUtilModel(
                type="file",
                name="movie.nfo",
                full_path="/movies/m1/movie.nfo",
                depth=2,
                file_type="nfo",
            ),
        ]
        filter_instance.nfo_parse_util.parse_nfo.return_value = {
            "title": "Interstellar",
            "plot": "A team of explorers travel through a wormhole in space",
            "director": "Christopher Nolan",
            "actors": ["Matthew McConaughey"],
            "genres": ["Sci-Fi", "Adventure"],
            "tags": ["Space"],
        }

        assert (
            len(
                filter_instance.apply_filters(
                    items, [{"filter": "NFO", "value": "wormhole"}]
                )
            )
            == 1
        )
        assert (
            len(
                filter_instance.apply_filters(
                    items, [{"filter": "NFO", "value": "McConaughey"}]
                )
            )
            == 1
        )
        assert (
            len(
                filter_instance.apply_filters(
                    items, [{"filter": "NFO", "value": "Nolan"}]
                )
            )
            == 1
        )
        assert (
            len(
                filter_instance.apply_filters(
                    items, [{"filter": "NFO", "value": "Nonexistent"}]
                )
            )
            == 0
        )
