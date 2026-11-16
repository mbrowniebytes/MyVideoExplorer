from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FfprobeVideo:
    """Video stream metadata extracted from ffprobe."""

    media_file_id: int
    stream_index: int
    width: int | None = None
    height: int | None = None
    codec_name: str | None = None
    codec_long_name: str | None = None
    profile: str | None = None
    pix_fmt: str | None = None
    framerate: str | None = None
    bitrate: int | None = None
    duration_s: float | None = None
    color_range: str | None = None
    color_space: str | None = None
    color_transfer: str | None = None
