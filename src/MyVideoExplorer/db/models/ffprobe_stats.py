from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FfprobeStats:
    probed_files: int
    video_streams: int
    audio_streams: int
    subtitle_streams: int
    last_probed: datetime | None
