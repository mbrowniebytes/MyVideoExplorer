from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FfprobeAudio:
    """Audio stream metadata extracted from ffprobe."""

    media_file_id: int
    stream_index: int
    codec_name: str | None = None
    profile: str | None = None
    channels: int | None = None
    channel_layout: str | None = None
    sample_rate: int | None = None
    bitrate: int | None = None
    lang: str | None = None
    default_track: bool | None = None
    forced: bool | None = None
