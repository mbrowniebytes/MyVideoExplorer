from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class TagStateProtocol(Protocol):
    tags: list[dict[str, str]]
    tags_changed: Any
    tag_counts_changed: Any

    def add_tag(self, tag: str) -> Any: ...


@dataclass(frozen=True)
class TagItem:
    tag: str
    color: str = "#808080"
    qty: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "color": self.color,
            "qty": self.qty,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TagItem:
        return cls(
            tag=str(data.get("tag", "")).strip(),
            color=str(data.get("color", "#808080")),
            qty=max(0, int(data.get("qty", 0) or 0)),
        )
