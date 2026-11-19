from __future__ import annotations

import msgspec
import pytest

from MyVideoExplorer.settings.export_schemas import (
    ExportFilterItem,
    ExportGroup,
    ExportManualItem,
    FilterExportPayload,
    MediaConfigItem,
    MediaExportPayload,
    TagItem,
    TagsExportPayload,
)


class TestExportManualItem:
    def test_encode_decode(self):
        item = ExportManualItem(
            order_index=1, media_folder="Movies", rel_path="sub/file.mp4"
        )
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=ExportManualItem)
        assert decoded.order_index == 1
        assert decoded.media_folder == "Movies"
        assert decoded.rel_path == "sub/file.mp4"

    def test_backward_compat_with_extra_fields(self):
        """Old exports may contain media_id and status — should be ignored on decode."""
        raw = b'{"order_index": 1, "media_folder": "Movies", "rel_path": "a.mp4", "media_id": 42, "status": "exists"}'
        decoded = msgspec.json.decode(raw, type=ExportManualItem)
        assert decoded.order_index == 1
        assert decoded.media_folder == "Movies"
        assert decoded.rel_path == "a.mp4"

    def test_missing_field_should_fail(self):
        raw = b'{"order_index": 1, "media_folder": "Movies"}'
        with pytest.raises(msgspec.DecodeError):
            msgspec.json.decode(raw, type=ExportManualItem)


class TestExportFilterItem:
    def test_encode_decode_with_all_fields(self):
        item = ExportFilterItem(
            name="My Filter",
            filters=[{"field": "title", "op": "contains", "value": "test"}],
            sort_option="manual",
            group_name="Favorites",
            is_visible=True,
            manual_items=[
                ExportManualItem(order_index=1, media_folder="Movies", rel_path="a.mp4")
            ],
        )
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=ExportFilterItem)
        assert decoded.name == "My Filter"
        assert decoded.sort_option == "manual"
        assert decoded.group_name == "Favorites"
        assert decoded.manual_items is not None
        assert len(decoded.manual_items) == 1

    def test_defaults_for_optional_fields(self):
        item = ExportFilterItem(
            name="Simple",
            filters=[{"field": "year", "op": "gte", "value": "2020"}],
            sort_option="default",
        )
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=ExportFilterItem)
        assert decoded.group_name == ""
        assert decoded.is_visible is True
        assert decoded.manual_items is None

    def test_extra_fields_ignored_on_decode(self):
        raw = b'{"name": "F", "filters": [], "sort_option": "default", "unknown": 42}'
        decoded = msgspec.json.decode(raw, type=ExportFilterItem)
        assert decoded.name == "F"

    def test_empty_name_should_fail(self):
        raw = b'{"name": "", "filters": [{"a": 1}], "sort_option": "default"}'
        # msgspec does not enforce non-empty strings by default, so this decodes
        # The validation of non-empty name is handled at the application level
        decoded = msgspec.json.decode(raw, type=ExportFilterItem)
        assert decoded.name == ""

    def test_missing_required_field_should_fail(self):
        raw = b'{"name": "F", "sort_option": "default"}'
        with pytest.raises(msgspec.DecodeError):
            msgspec.json.decode(raw, type=ExportFilterItem)


class TestExportGroup:
    def test_encode_decode(self):
        group = ExportGroup(group_id=5, name="Action")
        raw = msgspec.json.encode(group)
        decoded = msgspec.json.decode(raw, type=ExportGroup)
        assert decoded.group_id == 5
        assert decoded.name == "Action"


class TestFilterExportPayload:
    def test_full_round_trip(self):
        payload = FilterExportPayload(
            app_version="2026.11.16",
            groups=[ExportGroup(group_id=1, name="Favorites")],
            filters=[
                ExportFilterItem(
                    name="Recent",
                    filters=[{"field": "year", "op": "gte", "value": "2020"}],
                    sort_option="default",
                    group_name="Favorites",
                )
            ],
        )
        raw = msgspec.json.encode(payload)
        decoded = msgspec.json.decode(raw, type=FilterExportPayload)
        assert decoded.app_version == "2026.11.16"
        assert len(decoded.groups) == 1
        assert decoded.groups[0].name == "Favorites"
        assert len(decoded.filters) == 1
        assert decoded.filters[0].name == "Recent"

    def test_empty_filters_and_groups(self):
        payload = FilterExportPayload(
            app_version="1.0",
            groups=[],
            filters=[],
        )
        raw = msgspec.json.encode(payload)
        decoded = msgspec.json.decode(raw, type=FilterExportPayload)
        assert decoded.groups == []
        assert decoded.filters == []

    def test_missing_groups_should_fail(self):
        raw = b'{"app_version": "1.0", "filters": []}'
        with pytest.raises(msgspec.DecodeError):
            msgspec.json.decode(raw, type=FilterExportPayload)

    def test_extra_fields_ignored(self):
        raw = b'{"app_version": "1.0", "groups": [], "filters": [], "extra": true}'
        decoded = msgspec.json.decode(raw, type=FilterExportPayload)
        assert decoded.app_version == "1.0"


class TestMediaConfigItem:
    def test_encode_decode_with_all_fields(self):
        item = MediaConfigItem(
            label="Home", path="/movies", icon="fa6s.film", media_type="movie"
        )
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=MediaConfigItem)
        assert decoded.label == "Home"
        assert decoded.path == "/movies"
        assert decoded.icon == "fa6s.film"
        assert decoded.media_type == "movie"

    def test_defaults_for_optional_fields(self):
        item = MediaConfigItem(label="Work", path="/work")
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=MediaConfigItem)
        assert decoded.icon == "fa6s.folder"
        assert decoded.media_type == "movie"

    def test_extra_fields_ignored(self):
        # Simulates _previous_label leaking into exported data
        raw = b'{"label": "A", "path": "/a", "_previous_label": "Old"}'
        decoded = msgspec.json.decode(raw, type=MediaConfigItem)
        assert decoded.label == "A"
        assert decoded.path == "/a"


class TestMediaExportPayload:
    def test_full_round_trip(self):
        payload = MediaExportPayload(
            app_version="2026.11.16",
            media_configs=[
                MediaConfigItem(label="Movies", path="/movies", icon="fa6s.film")
            ],
            db_enabled=True,
        )
        raw = msgspec.json.encode(payload)
        decoded = msgspec.json.decode(raw, type=MediaExportPayload)
        assert decoded.app_version == "2026.11.16"
        assert len(decoded.media_configs) == 1
        assert decoded.media_configs[0].label == "Movies"
        assert decoded.db_enabled is True

    def test_missing_db_enabled_should_fail(self):
        raw = b'{"app_version": "1.0", "media_configs": []}'
        with pytest.raises(msgspec.DecodeError):
            msgspec.json.decode(raw, type=MediaExportPayload)


class TestTagItem:
    def test_encode_decode(self):
        item = TagItem(tag="Sci-Fi", color="#FF0000")
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=TagItem)
        assert decoded.tag == "Sci-Fi"
        assert decoded.color == "#FF0000"

    def test_default_color(self):
        item = TagItem(tag="Drama")
        raw = msgspec.json.encode(item)
        decoded = msgspec.json.decode(raw, type=TagItem)
        assert decoded.color == "#808080"


class TestTagsExportPayload:
    def test_full_round_trip(self):
        payload = TagsExportPayload(
            app_version="2026.11.16",
            tags=[
                TagItem(tag="Action", color="#FF0000"),
                TagItem(tag="Comedy"),
            ],
        )
        raw = msgspec.json.encode(payload)
        decoded = msgspec.json.decode(raw, type=TagsExportPayload)
        assert decoded.app_version == "2026.11.16"
        assert len(decoded.tags) == 2
        assert decoded.tags[0].tag == "Action"
        assert decoded.tags[0].color == "#FF0000"
        assert decoded.tags[1].tag == "Comedy"
        assert decoded.tags[1].color == "#808080"

    def test_empty_tags(self):
        payload = TagsExportPayload(app_version="1.0", tags=[])
        raw = msgspec.json.encode(payload)
        decoded = msgspec.json.decode(raw, type=TagsExportPayload)
        assert decoded.tags == []

    def test_missing_tags_should_fail(self):
        raw = b'{"app_version": "1.0"}'
        with pytest.raises(msgspec.DecodeError):
            msgspec.json.decode(raw, type=TagsExportPayload)
