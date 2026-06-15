from __future__ import annotations

from typing import Any


class MediaInfoIdLinkFormatter:
    """Formats known media IDs as small HTML links for label widgets."""

    KNOWN_EXTERNAL_ID_TYPES_WITHOUT_LABEL = {"imdbid", "tmdbid"}

    def build_id_html_values(self, media_id_items: list[dict[str, Any]]) -> list[str]:
        formatted_id_html_values: list[str] = []

        for media_id_item in media_id_items:
            media_id_type = media_id_item.get("type", "")
            media_id_value = media_id_item.get("id", "")

            if media_id_type == "imdbid":
                formatted_id_html_values.append(
                    f'<a href="https://www.imdb.com/title/{media_id_value}/">IMDb</a> '
                )
            elif media_id_type == "tmdbid":
                formatted_id_html_values.append(
                    f'<a href="https://www.themoviedb.org/movie/{media_id_value}/">TMDB</a> '
                )
            else:
                formatted_id_html_values.append(f"<i>{media_id_type}</i> ")

        return formatted_id_html_values

    def should_hide_id_label(self, media_id_type: str) -> bool:
        return media_id_type in self.KNOWN_EXTERNAL_ID_TYPES_WITHOUT_LABEL
