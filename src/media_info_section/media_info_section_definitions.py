from __future__ import annotations


MEDIA_INFO_SECTION_COMMON = "section_common"
MEDIA_INFO_SECTION_PLOT = "section_plot"
MEDIA_INFO_SECTION_IDS = "section_ids"
MEDIA_INFO_SECTION_VIDEOS = "section_videos"
MEDIA_INFO_SECTION_AUDIOS = "section_audios"
MEDIA_INFO_SECTION_SUBTITLES = "section_subtitles"
MEDIA_INFO_SECTION_ACTORS = "section_actors"

MEDIA_INFO_VIEW_MODE_DEFAULT = "media_info"
MEDIA_INFO_VIEW_MODE_IMAGE_LIST = "image_list"

MEDIA_INFO_CORE_SECTION_DEFINITIONS = [
    (MEDIA_INFO_SECTION_COMMON, "Common"),
    (MEDIA_INFO_SECTION_PLOT, "Plot"),
    (MEDIA_INFO_SECTION_IDS, "IDs"),
]

MEDIA_INFO_MEDIA_SECTION_DEFINITIONS = [
    (MEDIA_INFO_SECTION_VIDEOS, "Videos"),
    (MEDIA_INFO_SECTION_AUDIOS, "Audios"),
    (MEDIA_INFO_SECTION_SUBTITLES, "Subtitles"),
]

MEDIA_INFO_ACTORS_SECTION_DEFINITION = (MEDIA_INFO_SECTION_ACTORS, "Actors")

MEDIA_INFO_SECTIONS_HIDDEN_IN_IMAGE_LIST = [
    MEDIA_INFO_SECTION_VIDEOS,
    MEDIA_INFO_SECTION_AUDIOS,
    MEDIA_INFO_SECTION_SUBTITLES,
]


def get_media_info_toolbar_section_definitions(view_mode: str) -> list[tuple[str, str]]:
    section_definitions = list(MEDIA_INFO_CORE_SECTION_DEFINITIONS)

    if view_mode != MEDIA_INFO_VIEW_MODE_IMAGE_LIST:
        section_definitions.extend(MEDIA_INFO_MEDIA_SECTION_DEFINITIONS)

    section_definitions.append(MEDIA_INFO_ACTORS_SECTION_DEFINITION)
    return section_definitions
