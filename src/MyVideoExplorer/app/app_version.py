from __future__ import annotations

import re
from importlib.metadata import version

"""App version module.

Reads the version from `pyproject.toml` via `importlib.metadata` so the app
can report its version at runtime without parsing TOML directly.
Falls back to `"dev"` when the package is not installed (e.g., running
directly from source without `pip install -e .`).

The stored version uses PEP 440 CalVer format (e.g., `2026.11.16.008`),
but the display format matches GitHub releases (e.g., `20261116-008`).
"""


def _read_version() -> str:
    """Return the package version or a development fallback."""
    try:
        return version("MyVideoExplorer")
    except Exception:
        return "dev"


__version__: str = _read_version()


def format_version_for_display(version_str: str) -> str:
    """Convert the PEP 440 CalVer format to a GitHub release-friendly format.

    Converts `2026.11.16.008` to `20261116-008`.
    Returns the original string unchanged if it doesn't match the expected
    CalVer pattern or is a development version.
    """
    if not version_str or version_str == "dev":
        return version_str

    # Match CalVer pattern: YYYY.MM.DD.NNN
    match = re.match(r"^(\d{4})\.(\d{2})\.(\d{2})\.(\d+)$", version_str)
    if match:
        year, month, day, build = match.groups()
        return f"{year}{month}{day}-{build.zfill(3)}"
    return version_str


def get_app_metadata() -> dict[str, str]:
    """Return a dict with app metadata for display or export purposes."""
    return {
        "app_version": __version__,
    }
