from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FfprobeSubtitle:
    """Subtitle stream metadata extracted from ffprobe."""

    media_file_id: int
    stream_index: int
    format: str | None = None
    lang: str | None = None
    is_default: bool | None = None
    is_forced: bool | None = None
    title: str | None = None
