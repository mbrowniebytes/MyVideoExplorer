import os
from math import floor
from xml.etree import ElementTree

from src.utils.file_util import FileUtil


class NfoParseUtil:
    def __init__(self, file_util: FileUtil, log_util=None):
        super().__init__()
        self.file_util = file_util
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")
        self._cached_folder_path: str | None = None
        self._cached_movie_info: dict | None = None

    def parse_nfo(
        self, folder_path: str | None = None, nfo_file: str | None = None
    ) -> dict | None:
        if nfo_file is None and folder_path is None:
            print("NfoUtil: No NFO file or folder path provided")
            return None

        if nfo_file is None and folder_path is not None:
            return self.parse_nfo_folder(folder_path)

        if nfo_file is None:
            return None

        return self.parse_nfo_file(nfo_file)

    def parse_nfo_folder(self, folder_path: str) -> dict | None:
        if not folder_path:
            print("NfoUtil: No NFO folder provided")
            return None

        if self._cached_folder_path == folder_path:
            return self._cached_movie_info

        nfo_file = self.file_util.find_nfo_file(folder_path)
        if nfo_file is None:
            print("NfoUtil: No NFO file found")
            self._cached_folder_path = folder_path
            self._cached_movie_info = None
            return None

        movie_info = self.parse_nfo_file(nfo_file)
        self._cached_folder_path = folder_path
        self._cached_movie_info = movie_info
        return movie_info

    def parse_nfo_file(self, nfo_file: str) -> dict | None:
        if not nfo_file:
            return None

        if not os.path.isfile(nfo_file):
            print(f"NfoUtil: NFO file does not exist: {nfo_file}")
            return None

        try:
            tree = ElementTree.parse(nfo_file)
            root = tree.getroot()

            movie_info = self.create_empty_movie_info()
            self.extract_media_metadata(root, movie_info)
            return self.normalize_movie_info(movie_info)

        except ElementTree.ParseError as e:
            print(f"Error parsing NFO file '{nfo_file}': {e}")
            return None
        except OSError as e:
            print(f"Error reading NFO file '{nfo_file}': {e}")
            return None
        except Exception as e:
            print(f"Unexpected error parsing NFO file '{nfo_file}': {e}")
            return None

    def create_empty_movie_info(self) -> dict:
        return {
            "ids": [],
            "title": "",
            "year": 0,
            "plot": "",
            "outline": "",
            "mpaa": "",
            "videos": [],
            "audios": [],
            "subtitles": [],
            "source": "",
            "set": "",
            "rating": "",
            "runtime": "",
            "tagline": "",
            "genres": [],
            "directors": [],
            "actors": [],
        }

    def extract_media_metadata(
        self, root: ElementTree.Element, movie_info: dict | None = None
    ) -> dict:
        if movie_info is None:
            movie_info = self.create_empty_movie_info()

        self._parse_basic_fields(root, movie_info)
        self._parse_ids(root, movie_info)
        self._parse_set(root, movie_info)
        self._parse_genres(root, movie_info)
        self._parse_source(root, movie_info)
        self._parse_rating(root, movie_info)
        self._parse_stream_details(root, movie_info)
        self._parse_directors(root, movie_info)
        self._parse_actors(root, movie_info)
        return movie_info

    def normalize_movie_info(self, movie_info: dict) -> dict:
        self._dedupe_movie_info(movie_info)
        return movie_info

    def _parse_basic_fields(self, root: ElementTree.Element, movie_info: dict) -> None:
        for field_name in ["title", "plot", "mpaa", "outline", "runtime", "tagline"]:
            movie_info[field_name] = self._clean_text(root.findtext(field_name, ""))

        movie_info["year"] = self._to_int(root.findtext("year", "0"))

    def _parse_ids(self, root: ElementTree.Element, movie_info: dict) -> None:
        uniqueid_nodes = root.findall("uniqueid")
        if uniqueid_nodes:
            for uniqueid in uniqueid_nodes:
                site_type = self._clean_text(uniqueid.get("type", "")).lower()
                site_id = self._clean_text(uniqueid.text)
                site_info = self._parse_site_type_ids(site_type, site_id)
                if site_info:
                    movie_info["ids"].append(site_info)

            return

        fallback_ids = [
            ("tmdbId", "tmdbid"),
            ("tmdbid", "tmdbid"),
            ("tmdb", "tmdbid"),
        ]
        for tag_name, site_type in fallback_ids:
            site_id = self._clean_text(root.findtext(tag_name, ""))
            site_info = self._parse_site_type_ids(site_type, site_id)
            if site_info:
                movie_info["ids"].append(site_info)

        fallback_ids = [
            ("imdbid", "imdbid"),
            ("imdb", "imdbid"),
        ]
        for tag_name, site_type in fallback_ids:
            site_id = self._clean_text(root.findtext(tag_name, ""))
            site_info = self._parse_site_type_ids(site_type, site_id)
            if site_info:
                movie_info["ids"].append(site_info)

        fallback_ids = [
            ("id", "id"),
        ]
        for tag_name, site_type in fallback_ids:
            site_id = self._clean_text(root.findtext(tag_name, ""))
            site_info = self._parse_site_type_ids(site_type, site_id)
            if site_info:
                movie_info["ids"].append(site_info)

    def _parse_site_type_ids(self, site_type: str, site_id: str) -> dict:
        site_info = {}
        if site_id:
            if site_type == "tmdb":
                site_type = "tmdbid"
            elif site_type == "imdb":
                site_type = "imdbid"
            elif site_id.startswith("tt"):
                site_type = "imdbid"
            site_info = {"type": site_type, "id": site_id}

        if not self._has_meaningful_dict_value(site_info):
            site_info = {}

        return site_info

    def _parse_set(self, root: ElementTree.Element, movie_info: dict) -> None:
        set_elem = root.find("set")
        if set_elem is None:
            return

        set_name = self._clean_text(set_elem.findtext("name", ""))
        if not set_name:
            set_name = self._clean_text(root.findtext("set", ""))

        movie_info["set"] = set_name

    def _parse_genres(self, root: ElementTree.Element, movie_info: dict) -> None:
        for genre in root.findall("genre"):
            value = self._clean_text(genre.text)
            if value:
                movie_info["genres"].append(value)

    def _parse_source(self, root: ElementTree.Element, movie_info: dict) -> None:
        source_elem = root.find("generator")
        if source_elem is None:
            return

        app_name = self._clean_text(source_elem.findtext("appname", ""))
        app_version = self._clean_text(source_elem.findtext("appversion", ""))

        if app_name == "MediaElch" and app_version:
            movie_info["source"] = f"{app_name};{app_version}"
        else:
            movie_info["source"] = app_name

    def _parse_rating(self, root: ElementTree.Element, movie_info: dict) -> None:
        ratings_elem = root.find("ratings")
        if ratings_elem is not None:
            rating_elem = ratings_elem.find("rating")
            if rating_elem is not None:
                movie_info["rating"] = self._clean_text(
                    rating_elem.findtext("value", "")
                )

        if not movie_info["rating"]:
            movie_info["rating"] = self._clean_text(root.findtext("rating", ""))

    def _parse_stream_details(
        self, root: ElementTree.Element, movie_info: dict
    ) -> None:
        stream_root = root.find("fileinfo/streamdetails")

        video_nodes = []
        if stream_root is not None:
            video_nodes.extend(stream_root.findall("video"))
        video_nodes.extend(root.findall("video"))
        for video_elem in video_nodes:
            movie_info["videos"].append(self._parse_video(video_elem))

        audio_nodes = []
        if stream_root is not None:
            audio_nodes.extend(stream_root.findall("audio"))
        audio_nodes.extend(root.findall("audio"))
        for audio_elem in audio_nodes:
            movie_info["audios"].append(self._parse_audio(audio_elem))

        subtitle_nodes = []
        if stream_root is not None:
            subtitle_nodes.extend(stream_root.findall("subtitle"))
        subtitle_nodes.extend(root.findall("subtitle"))
        for subtitle_elem in subtitle_nodes:
            movie_info["subtitles"].append(self._parse_subtitle(subtitle_elem))

    def _parse_video(self, video_elem: ElementTree.Element) -> dict:
        width = self._to_int(video_elem.findtext("width", "0"))
        height = self._to_int(video_elem.findtext("height", "0"))
        resolution_label, format_label = self._video_labels(width, height)

        return {
            "codec": self._clean_text(video_elem.findtext("codec", "")),
            "bitrate": self._to_int(video_elem.findtext("bitrate", "0")),
            "runtime": floor(
                self._to_int(video_elem.findtext("durationinseconds", "0")) / 60
            ),
            "language": self._clean_text(video_elem.findtext("language", "")),
            "aspect": self._to_float(video_elem.findtext("aspect", "0.0")),
            "width": width,
            "height": height,
            "resolution": resolution_label,
            "format": format_label,
        }

    def _parse_audio(self, audio_elem: ElementTree.Element) -> dict:
        return {
            "codec": self._clean_text(audio_elem.findtext("codec", "")),
            "bitrate": self._to_int(audio_elem.findtext("bitrate", "0")),
            "language": self._clean_text(audio_elem.findtext("language", "")),
            "channels": self._to_int(audio_elem.findtext("channels", "0")),
        }

    def _parse_subtitle(self, subtitle_elem: ElementTree.Element) -> dict:
        return {"language": self._clean_text(subtitle_elem.findtext("language", ""))}

    def _parse_directors(self, root: ElementTree.Element, movie_info: dict) -> None:
        for director in root.findall("director"):
            value = self._clean_text(director.text)
            if value:
                movie_info["directors"].append(value)

    def _parse_actors(self, root: ElementTree.Element, movie_info: dict) -> None:
        for actor in root.findall("actor"):
            actor_data = {
                "name": self._clean_text(actor.findtext("name", "")),
                "role": self._clean_text(actor.findtext("role", "")),
                "order": self._to_int(actor.findtext("order", "0")),
                "thumb": self._clean_text(actor.findtext("thumb", "")),
            }
            if self._has_meaningful_dict_value(actor_data):
                movie_info["actors"].append(actor_data)

    def _dedupe_movie_info(self, movie_info: dict) -> None:
        movie_info["ids"] = self._dedupe_dict_list(movie_info["ids"])
        movie_info["videos"] = self._dedupe_dict_list(movie_info["videos"])
        movie_info["audios"] = self._dedupe_dict_list(movie_info["audios"])
        movie_info["subtitles"] = self._dedupe_dict_list(movie_info["subtitles"])
        movie_info["actors"] = self._dedupe_dict_list(movie_info["actors"])
        movie_info["genres"] = self._dedupe_str_list(movie_info["genres"])
        movie_info["directors"] = self._dedupe_str_list(movie_info["directors"])

    def _dedupe_str_list(self, values: list[str]) -> list[str]:
        result = []
        seen = set()
        for value in values:
            cleaned = self._clean_text(value)
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            result.append(cleaned)
        return result

    def _dedupe_dict_list(self, rows: list[dict]) -> list[dict]:
        result = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            cleaned_row = self._clean_dict_values(row)
            if not self._has_meaningful_dict_value(cleaned_row):
                continue
            row_key = tuple(sorted(cleaned_row.items()))
            if row_key in seen:
                continue
            seen.add(row_key)
            result.append(cleaned_row)
        return result

    def _clean_dict_values(self, row: dict) -> dict:
        cleaned = {}
        for key, value in row.items():
            if isinstance(value, str):
                cleaned[key] = self._clean_text(value)
            else:
                cleaned[key] = value
        return cleaned

    def _has_meaningful_value(self, value: str | int | float) -> bool:
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, (int, float)) and value != 0:
            return True
        return False

    def _has_meaningful_dict_value(self, row: dict) -> bool:
        for value in row.values():
            if self._has_meaningful_value(value):
                return True
        return False

    def _video_labels(self, width: int, height: int) -> tuple[str, str]:
        if width <= 350 or height <= 240:
            return "tiny", "tiny"
        if width <= 720 or height <= 480:
            return "sd", "dvd"
        if width <= 1280 or height <= 720:
            return "hd", "bluray"
        if width <= 1920 or height <= 1080:
            return "fhd", "bluray"
        if width <= 2560 or height <= 1440:
            return "2k", "2k"
        if width <= 4096 or height <= 2160:
            return "4k", "4k"
        if width <= 5120 or height <= 2880:
            return "5k", "5k"
        if width <= 7680 or height <= 4320:
            return "8k", "8k"
        return "", ""

    def _clean_text(self, value: str | None) -> str:
        if value is None:
            return ""
        return value.strip()

    def _to_int(self, value: str | None, default: int = 0) -> int:
        try:
            return int((value or "").strip())
        except (TypeError, ValueError):
            return default

    def _to_float(self, value: str | None, default: float = 0.0) -> float:
        try:
            return float((value or "").strip())
        except (TypeError, ValueError):
            return default
