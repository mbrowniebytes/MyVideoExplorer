from __future__ import annotations

from pathlib import Path
from typing import Any

# Package-local defaults directory where built-in config files live.
PACKAGE_CFG_DIR = Path(__file__).resolve().parent / "cfg"
PLAYLISTS_FILE = PACKAGE_CFG_DIR / "filters_playlists.json"


def load_playlists_from_json(
    filter_store: Any,
    json_util: Any,
    saved_filters: list[dict[str, Any]] | None = None,
    on_filters_changed: Any = None,
) -> list[dict[str, Any]]:
    """Load playlist templates from JSON and sync them as system filters.

    Reads the predefined playlist templates from ``filters_playlists.json``
    and synchronizes them as system filters.  Each playlist entry specifies
    its own group via the ``group`` field.  If a filter with the same name
    already exists and is marked ``is_system=True``, it is updated.  If the
    entry contains ``"action": "delete"``, the filter is removed if found.

    Args:
        filter_store: A ``DbFilters`` instance for persistence operations.
        json_util: A ``JsonUtil`` instance for loading JSON files.
        saved_filters: Optional current filter list (used only for return).
        on_filters_changed: Optional callable to invoke after sync completes.

    Returns:
        The refreshed list of all filters after sync.
    """
    if not PLAYLISTS_FILE.exists():
        return _refresh_filters(filter_store, saved_filters, on_filters_changed)

    data = json_util.load_json(PLAYLISTS_FILE)

    # Support both formats: flat array or {"playlists": [...]}
    playlists = data if isinstance(data, list) else data.get("playlists", [])

    if not playlists:
        return _refresh_filters(filter_store, saved_filters, on_filters_changed)

    # Build a group name -> group_id cache
    groups = filter_store.list_groups()
    group_cache: dict[str, int] = {g["name"]: g["group_id"] for g in groups}

    def ensure_group(name: str) -> int:
        """Return the group_id for *name*, creating it if missing."""
        if name in group_cache:
            return group_cache[name]
        group_id = filter_store.create_group(name)
        group_cache[name] = group_id
        # Mark as system group
        with filter_store._connect() as con:
            con.execute(
                "UPDATE filter_groups SET is_system = TRUE WHERE group_id = ?",
                (group_id,),
            )
        return group_id

    # Collect all existing filters for update/delete matching
    existing_filters = filter_store.list_filters()
    existing_by_name: dict[str, dict[str, Any]] = {
        f["name"].casefold(): f for f in existing_filters
    }

    for playlist in playlists:
        name = str(playlist.get("name", "")).strip()
        if not name:
            continue

        # Handle delete action
        action = str(playlist.get("action", "")).strip().lower()
        if action == "delete":
            existing = existing_by_name.get(name.casefold())
            if existing is not None:
                filter_store.delete_filter(name)
            existing_by_name.pop(name.casefold(), None)
            continue

        filters = playlist.get("filters", [])
        sort_option = playlist.get("sort_option", "default")
        group_name = str(playlist.get("group", "Playlists")).strip()
        if not group_name:
            group_name = "Playlists"
        if not filters:
            continue

        group_id = ensure_group(group_name)

        # Check if this is an update to an existing system filter
        existing = existing_by_name.get(name.casefold())
        original_name = name if existing is not None else None

        filter_store.save_filter(
            name,
            filters,
            original_name=original_name,
            sort_option=sort_option,
            group_id=group_id,
            is_system=True,
            is_visible=True,
        )

    return _refresh_filters(filter_store, saved_filters, on_filters_changed)


def _refresh_filters(
    filter_store: Any,
    saved_filters: list[dict[str, Any]] | None,
    on_filters_changed: Any,
) -> list[dict[str, Any]]:
    """Refresh the filter list and optionally emit a changed signal."""
    filters = filter_store.list_filters()
    if on_filters_changed is not None:
        on_filters_changed()
    return filters
