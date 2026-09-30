from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class MediaFileMetadata:
    title: str | None
    year: int | None
    plot: str | None
    score: Decimal | None
    rated: str | None
    runtime: int | None
    tags: list[str] | None
    genres: list[str] | None
    actors: list[str] | None
    directors: list[str] | None

    def to_movie_info(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "year": self.year,
            "plot": self.plot,
            "score": self.score,
            "rated": self.rated,
            "runtime": self.runtime,
            "tags": self.tags,
            "genres": self.genres,
            "actors": self.actors,
            "director": ", ".join(self.directors or []),
        }
