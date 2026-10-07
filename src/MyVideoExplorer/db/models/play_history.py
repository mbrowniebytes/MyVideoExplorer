from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PlayHistory:
    qty_played: int
    last_played: date | None
