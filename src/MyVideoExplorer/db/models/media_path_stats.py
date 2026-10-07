from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MediaPathStats:
    media_path: str
    subfolders_count: int | None
    files_count: int | None
    images_count: int | None
    videos_count: int | None
    nfo_count: int | None
    other_count: int | None
    last_scanned: datetime | None
