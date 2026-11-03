from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from MyVideoExplorer.db.db_filters import DbFilters
from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.tag_cloud.tag_util import validate_name

# --- validate_name tests ---


def test_validate_name_accepts_valid_names():
    assert validate_name("Action") == (True, "")
    assert validate_name("My-Filter") == (True, "")
    assert validate_name("test_123") == (True, "")
    assert validate_name("a!b@c#") == (True, "")
    assert validate_name("name(with)parens") == (True, "")
    assert validate_name("---") == (True, "")
    assert validate_name("___") == (True, "")


def test_validate_name_rejects_slashes():
    is_valid, _ = validate_name("path/to")
    assert is_valid is False
    is_valid, _ = validate_name("back\\slash")
    assert is_valid is False


def test_validate_name_rejects_quotes():
    is_valid, _ = validate_name("it's")
    assert is_valid is False
    is_valid, _ = validate_name('say "hello"')
    assert is_valid is False


def test_validate_name_rejects_empty():
    is_valid, msg = validate_name("")
    assert is_valid is False
    assert "cannot be empty" in msg
    is_valid, msg = validate_name("   ")
    assert is_valid is False


# --- SettingsState media config validation tests ---


def _make_settings_state(tmp_path: Path) -> SettingsState:
    """Create a SettingsState with paths pointing to tmp_path."""
    import MyVideoExplorer.settings.settings_state as ss

    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    orig_cfg_dir = ss.CFG_DIR
    orig_pkg_cfg_dir = ss.PACKAGE_CFG_DIR
    try:
        ss.CFG_DIR = cfg_dir
        ss.PACKAGE_CFG_DIR = cfg_dir / "defaults"
        for name in (
            "SETTINGS_STATE_FILE",
            "SETTINGS_APP_FILE",
            "SETTINGS_UI_FILE",
            "SETTINGS_MEDIA_FILE",
            "SETTINGS_FILTER_FILE",
        ):
            setattr(
                ss, name, cfg_dir / f"{name.removeprefix('SETTINGS_').lower()}.json"
            )
        for name in (
            "DEFAULTS_STATE_FILE",
            "DEFAULTS_APP_FILE",
            "DEFAULTS_UI_FILE",
            "DEFAULTS_MEDIA_FILE",
            "DEFAULTS_FILTER_FILE",
        ):
            setattr(
                ss,
                name,
                cfg_dir / "defaults" / f"{name.removeprefix('DEFAULTS_').lower()}.json",
            )
        state = SettingsState(MagicMock(), filter_db_path=tmp_path / "filter.db")
        return state
    finally:
        ss.CFG_DIR = orig_cfg_dir
        ss.PACKAGE_CFG_DIR = orig_pkg_cfg_dir


def test_validate_media_configs_detects_duplicate_paths(tmp_path):
    state = _make_settings_state(tmp_path)
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    configs = [
        {"label": "Movies", "path": str(media_dir)},
        {"label": "TV Shows", "path": str(media_dir)},
    ]
    errors = state.validate_media_configs(configs)
    assert any("already registered" in err for err in errors)


def test_validate_media_configs_detects_duplicate_names_case_insensitive(tmp_path):
    state = _make_settings_state(tmp_path)
    media_dir1 = tmp_path / "media1"
    media_dir1.mkdir()
    media_dir2 = tmp_path / "media2"
    media_dir2.mkdir()
    configs = [
        {"label": "Movies", "path": str(media_dir1)},
        {"label": "movies", "path": str(media_dir2)},
    ]
    errors = state.validate_media_configs(configs)
    assert any("unique" in err.lower() for err in errors)


def test_validate_media_configs_rejects_invalid_name_characters(tmp_path):
    state = _make_settings_state(tmp_path)
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    configs = [
        {"label": "Path/To/Movies", "path": str(media_dir)},
    ]
    errors = state.validate_media_configs(configs)
    assert any("invalid name" in err.lower() for err in errors)


def test_validate_media_configs_accepts_valid_configs(tmp_path):
    state = _make_settings_state(tmp_path)
    media_dir1 = tmp_path / "media1"
    media_dir1.mkdir()
    media_dir2 = tmp_path / "media2"
    media_dir2.mkdir()
    configs = [
        {"label": "Movies", "path": str(media_dir1)},
        {"label": "TV-Shows", "path": str(media_dir2)},
    ]
    errors = state.validate_media_configs(configs)
    assert errors == []


# --- DbFilters validation tests ---


def _make_filter_store(tmp_path: Path) -> DbFilters:
    """Create a DbFilters instance with a temp database."""
    state = MagicMock()
    state.media_configs = []
    return DbFilters(state, [], db_path=tmp_path / "filter.db")


def test_save_filter_rejects_invalid_name_characters(tmp_path):
    store = _make_filter_store(tmp_path)
    try:
        store.save_filter("Path/To/Filter", [])
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Name may only contain" in str(exc)


def test_save_filter_rejects_duplicate_names_case_insensitive(tmp_path):
    store = _make_filter_store(tmp_path)
    store.save_filter("MyFilter", [])
    try:
        store.save_filter("myfilter", [])
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "already exists" in str(exc)


def test_save_filter_allows_rename_to_same_name_case(tmp_path):
    store = _make_filter_store(tmp_path)
    store.save_filter("MyFilter", [])
    # Renaming to the same name (different case) should work if it's the same filter
    store.save_filter("MyFilter", [], original_name="MyFilter")
    filters = store.list_filters()
    assert len(filters) == 1


def test_save_filter_rejects_name_with_quotes(tmp_path):
    store = _make_filter_store(tmp_path)
    try:
        store.save_filter("Filter's", [])
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Name may only contain" in str(exc)
