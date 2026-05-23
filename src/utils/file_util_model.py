from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FileUtilModelType = Literal["dir", "file"]


@dataclass(slots=True)
class FileUtilModel:
    type: FileUtilModelType
    name: str
    full_path: str
    depth: int = 0
    file_type: str | None = None

    @property
    def is_dir(self) -> bool:
        return self.type == "dir"

    @property
    def is_file(self) -> bool:
        return self.type == "file"
