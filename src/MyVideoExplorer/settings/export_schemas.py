from __future__ import annotations

from typing import Any

import msgspec


class ExportManualItem(msgspec.Struct):
    """A single manual sort item within a filter.

    Only portable fields are exported: media_folder and rel_path.
    The media_id is resolved from the target database on import.
    """

    order_index: int
    media_folder: str
    rel_path: str


class ExportFilterItem(msgspec.Struct):
    """A filter entry in an exported filter JSON payload."""

    name: str
    filters: list[dict[str, Any]]
    sort_option: str
    group_name: str = ""
    is_visible: bool = True
    manual_items: list[ExportManualItem] | None = None


class ExportGroup(msgspec.Struct):
    """A filter group entry in an exported filter JSON payload."""

    group_id: int
    name: str


class FilterExportPayload(msgspec.Struct):
    """Top-level payload for exported/imported filter JSON files."""

    app_version: str
    groups: list[ExportGroup]
    filters: list[ExportFilterItem]


class MediaConfigItem(msgspec.Struct):
    """A media folder config entry in an exported media JSON payload."""

    label: str
    path: str
    icon: str = "fa6s.folder"
    media_type: str = "movie"


class MediaExportPayload(msgspec.Struct):
    """Top-level payload for exported/imported media settings JSON files."""

    app_version: str
    media_configs: list[MediaConfigItem]
    db_enabled: bool


class TagItem(msgspec.Struct):
    """A tag entry in an exported tags JSON payload."""

    tag: str
    color: str = "#808080"


class TagsExportPayload(msgspec.Struct):
    """Top-level payload for exported/imported tags JSON files."""

    app_version: str
    tags: list[TagItem]
