import os
import threading
from math import floor
from typing import Any
from xml.etree import ElementTree
from src.utils.file_util import FileUtil


class NfoParseUtil:
    # Default movie info schema as a constant for better maintainability
    MOVIE_INFO_SCHEMA: dict[str, Any] = {
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

    def __init__(self, file_util: FileUtil, log_util: Any = None) -> None:
        super().__init__()
        self.file_util = file_util
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")
        self._cached_folder_path: str | None = None
        self._cached_movie_info: dict[str, Any] | None = None

    def parse_nfo(
        self, folder_path: str | None = None, nfo_file: str | None = None
    ) -> dict[str, Any] | None:
        """Parse NFO file or folder for movie information."""
        if not any([nfo_file, folder_path]):
            print("NfoUtil: No NFO file or folder path provided")
            return None

        # Prefer explicit nfo_file parameter
        if nfo_file:
            return self.parse_nfo_file(nfo_file)

        if folder_path:
            return self.parse_nfo_folder(folder_path)

        return None

    def parse_nfo_folder(self, folder_path: str) -> dict[str, Any] | None:
        """Parse NFO file from a folder path using cached result when possible."""
        if not folder_path:
            print("NfoUtil: No NFO folder provided")
            return None

        # Use cache if available
        if (
            self._cached_folder_path == folder_path
            and self._cached_movie_info is not None
        ):
            return self._cached_movie_info

        nfo_file = self.file_util.find_nfo_file(folder_path)
        if nfo_file is None:
            # print("NfoUtil: No NFO file found")
            # Cache the negative result
            self._cached_folder_path = folder_path
            self._cached_movie_info = None
            return None

        movie_info = self.parse_nfo_file(nfo_file)
        # Update cache with successful parse result
        self._cached_folder_path = folder_path
        self._cached_movie_info = movie_info
        return movie_info

    def parse_nfo_file(self, nfo_file: str) -> dict[str, Any] | None:
        """Parse NFO file and extract movie information."""
        if not nfo_file:
            return None

        if not os.path.isfile(nfo_file):
            print(f"NfoUtil: NFO file does not exist: {nfo_file}")
            return None

        # We'll run the blocking code in a thread and return the result (synchronously)
        result_container = []
        result_container.append(None)
        def thread_worker():
            try:
                tree = ElementTree.parse(nfo_file)
                root = tree.getroot()

                movie_info = self.create_empty_movie_info()
                self.extract_media_metadata(root, movie_info)
                result_container[0] = self.normalize_movie_info(movie_info)
            except ElementTree.ParseError as e:
                result_container[0] = None
                err = f"Error parsing NFO file '{nfo_file}': {e}"
                result_container.append(err)
            except OSError as e:
                result_container[0] = None
                err = f"Error reading NFO file '{nfo_file}': {e}"
                result_container.append(err)
            except Exception as e:
                # Store exception for detailed printing later
                result_container[0] = None
                err = f"Unexpected error parsing NFO file '{nfo_file}': {e}"
                result_container.append(err)

        thread = threading.Thread(target=thread_worker)
        thread.start()
        thread.join()  # Wait for the thread to finish

        # Print error details if parsing failed
        if len(result_container) > 1 and result_container[0] is None:
            print(f"{result_container[1]}")

        return result_container[0]

    def create_empty_movie_info(self) -> dict[str, Any]:
        """Create an empty movie info dictionary following the schema."""
        # Return a deep copy of the schema to avoid reference issues
        import copy

        return copy.deepcopy(self.MOVIE_INFO_SCHEMA)

    def extract_media_metadata(
        self, root: ElementTree.Element, movie_info: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Extract all media metadata from XML root into movie info."""
        if movie_info is None:
            movie_info = self.create_empty_movie_info()

        # dev test
        # sleep(2)

        # Parse all metadata sections in logical order
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

    def normalize_movie_info(self, movie_info: dict[str, Any]) -> dict[str, Any]:
        """Normalize and deduplicate movie info."""
        self._dedupe_movie_info(movie_info)
        return movie_info

    # --- Basic fields parsing ---

    def _parse_basic_fields(self, root: ElementTree.Element, movie_info: dict[str, Any]) -> None:
        """Parse basic text fields and year from NFO root."""
        for field_name in ["title", "plot", "mpaa", "outline", "runtime", "tagline"]:
            value = root.findtext(field_name)
            movie_info[field_name] = self._clean_text(value)

        # Parse year as integer
        year_str = root.findtext("year")
        movie_info["year"] = self._to_int(year_str, default=0)

    # --- ID parsing ---

    def _parse_ids(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse unique IDs from NFO root."""
        # Try to parse uniqueid elements first
        uniqueid_nodes = root.findall("uniqueid")
        if uniqueid_nodes:
            for uniqueid in uniqueid_nodes:
                site_type = self._clean_text(uniqueid.get("type", "")).lower()
                site_id = self._clean_text(uniqueid.text)
                site_info = self._parse_site_type_ids(site_type, site_id)
                if site_info and site_info not in movie_info["ids"]:
                    movie_info["ids"].append(site_info)
            return

        # Fallback IDs with priority order
        fallback_priority = [
            ("tmdbId", "tmdbid"),
            ("tmdbid", "tmdbid"),
            ("tmdb", "tmdbid"),
            ("imdbid", "imdbid"),
            ("imdb", "imdbid"),
            ("id", "id"),
        ]

        for tag_name, site_type in fallback_priority:
            site_id = self._clean_text(root.findtext(tag_name, ""))
            site_info = self._parse_site_type_ids(site_type, site_id)
            if site_info and site_info not in movie_info["ids"]:
                movie_info["ids"].append(site_info)

    def _parse_site_type_ids(self, site_type: str, site_id: str) -> dict | None:
        """Convert site type and ID into standardized format."""
        if not site_id:
            return None

        # Normalize known site types
        normalized_type = {"tmdb": "tmdbid", "imdb": "imdbid"}.get(site_type, site_type)

        # Detect IMDB IDs by prefix
        if site_id.startswith("tt") and normalized_type == site_type:
            normalized_type = "imdbid"

        return {"type": normalized_type, "id": site_id}

    # --- Set parsing ---

    def _parse_set(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse movie set information."""
        set_elem = root.find("set")
        if set_elem is None:
            return

        # Try nested name field first, then fallback to direct text
        set_name = self._clean_text(set_elem.findtext("name", ""))
        if not set_name:
            set_name = self._clean_text(set_elem.text)

        movie_info["set"] = set_name

    # --- Genre parsing ---

    def _parse_genres(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse genres from NFO root."""
        for genre in root.findall("genre"):
            value = self._clean_text(genre.text)
            if value and value not in movie_info["genres"]:
                movie_info["genres"].append(value)

    # --- Source parsing ---

    def _parse_source(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse source application information."""
        source_elem = root.find("generator")
        if source_elem is None:
            return

        app_name = self._clean_text(source_elem.findtext("appname", ""))
        app_version = self._clean_text(source_elem.findtext("appversion", ""))

        if app_name == "MediaElch" and app_version:
            movie_info["source"] = f"{app_name};{app_version}"
        elif app_name:
            movie_info["source"] = app_name

    # --- Rating parsing ---

    def _parse_rating(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse rating information from NFO root."""
        ratings_elem = root.find("ratings")
        if ratings_elem is not None:
            rating_elem = ratings_elem.find("rating")
            if rating_elem is not None:
                value = self._clean_text(rating_elem.findtext("value", ""))
                if value:
                    movie_info["rating"] = value

        # Fallback to direct rating element
        if not movie_info["rating"]:
            rating_value = root.findtext("rating")
            movie_info["rating"] = self._clean_text(rating_value)

    # --- Stream details parsing ---

    def _parse_stream_details(
        self, root: ElementTree.Element, movie_info: dict
    ) -> None:
        """Parse video/audio/subtitle stream details from NFO root."""
        stream_root = root.find("fileinfo/streamdetails")

        # Try to parse from streamdetails first, fallback to direct children
        if stream_root is not None:
            self._parse_stream_children(stream_root, "video", movie_info["videos"])
            self._parse_stream_children(stream_root, "audio", movie_info["audios"])
            self._parse_stream_children(
                stream_root, "subtitle", movie_info["subtitles"]
            )

        # Fallback to parsing from root directly
        self._parse_stream_children(
            root, "video", movie_info["videos"], is_fallback=True
        )
        self._parse_stream_children(
            root, "audio", movie_info["audios"], is_fallback=True
        )
        self._parse_stream_children(
            root, "subtitle", movie_info["subtitles"], is_fallback=True
        )

    def _parse_stream_children(
        self,
        root: ElementTree.Element,
        tag_name: str,
        target_list: list,
        is_fallback: bool = False,
    ) -> None:
        """Parse stream elements from root and add to target list."""
        for elem in root.findall(tag_name):
            if tag_name == "video":
                stream_info = self._parse_video(elem)
            elif tag_name == "audio":
                stream_info = self._parse_audio(elem)
            elif tag_name == "subtitle":
                stream_info = self._parse_subtitle(elem)
            else:
                continue

            # Avoid duplicate entries
            if stream_info not in target_list:
                target_list.append(stream_info)

    def _parse_video(self, video_elem: ElementTree.Element) -> dict:
        """Parse video stream information."""
        width = self._to_int(video_elem.findtext("width"), default=0)
        height = self._to_int(video_elem.findtext("height"), default=0)
        resolution_label, format_label = self._video_labels(width, height)

        duration_str = video_elem.findtext("durationinseconds")
        duration_minutes = floor(self._to_int(duration_str, default=0) / 60)

        return {
            "codec": self._clean_text(video_elem.findtext("codec")),
            "bitrate": self._to_int(video_elem.findtext("bitrate"), default=0),
            "runtime": duration_minutes,
            "language": self._clean_text(video_elem.findtext("language")),
            "aspect": self._to_float(video_elem.findtext("aspect"), default=0.0),
            "width": width,
            "height": height,
            "resolution": resolution_label,
            "format": format_label,
        }

    def _parse_audio(self, audio_elem: ElementTree.Element) -> dict:
        """Parse audio stream information."""
        return {
            "codec": self._clean_text(audio_elem.findtext("codec")),
            "bitrate": self._to_int(audio_elem.findtext("bitrate"), default=0),
            "language": self._clean_text(audio_elem.findtext("language")),
            "channels": self._to_int(audio_elem.findtext("channels"), default=0),
        }

    def _parse_subtitle(self, subtitle_elem: ElementTree.Element) -> dict:
        """Parse subtitle information."""
        return {"language": self._clean_text(subtitle_elem.findtext("language"))}

    # --- People parsing ---

    def _parse_directors(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse director information from NFO root."""
        for director in root.findall("director"):
            value = self._clean_text(director.text)
            if value and value not in movie_info["directors"]:
                movie_info["directors"].append(value)

    def _parse_actors(self, root: ElementTree.Element, movie_info: dict) -> None:
        """Parse actor information from NFO root."""
        for actor in root.findall("actor"):
            name = self._clean_text(actor.findtext("name"))
            if not name:
                continue

            actor_data = {
                "name": name,
                "role": self._clean_text(actor.findtext("role")),
                "order": self._to_int(actor.findtext("order"), default=0),
                "thumb": self._clean_text(actor.findtext("thumb")),
            }

            # Only add if we have meaningful data
            if self._has_meaningful_dict_value(actor_data):
                movie_info["actors"].append(actor_data)

    # --- Deduplication ---

    def _dedupe_movie_info(self, movie_info: dict) -> None:
        """Deduplicate all list fields in movie info."""
        for key in ["ids", "videos", "audios", "subtitles", "actors"]:
            original_list = movie_info.get(key, [])
            movie_info[key] = self._dedupe_dict_list(original_list)

        for key in ["genres", "directors"]:
            original_list = movie_info.get(key, [])
            movie_info[key] = self._dedupe_str_list(original_list)

    def _dedupe_str_list(self, values: list[str]) -> list[str]:
        """Remove duplicates from a string list while preserving order."""
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
        """Remove duplicate dictionaries from a list while preserving order."""
        result = []
        seen_keys = set()

        for row in rows:
            if not isinstance(row, dict):
                continue

            cleaned_row = self._clean_dict_values(row)
            if not self._has_meaningful_dict_value(cleaned_row):
                continue

            # Create a hashable key from sorted items
            row_key = tuple(sorted(cleaned_row.items()))
            if row_key in seen_keys:
                continue

            seen_keys.add(row_key)
            result.append(cleaned_row)

        return result

    def _clean_dict_values(self, row: dict) -> dict:
        """Recursively clean string values in a dictionary."""
        cleaned = {}
        for key, value in row.items():
            if isinstance(value, str):
                cleaned[key] = self._clean_text(value)
            else:
                cleaned[key] = value
        return cleaned

    # --- Validation helpers ---

    def _has_meaningful_value(self, value) -> bool:
        """Check if a value is considered meaningful (non-empty string or non-zero number)."""
        if isinstance(value, str) and value.strip():
            return True
        if isinstance(value, (int, float)) and value != 0:
            return True
        return False

    def _has_meaningful_dict_value(self, row: dict) -> bool:
        """Check if a dictionary has at least one meaningful value."""
        return any(self._has_meaningful_value(v) for v in row.values())

    # --- Utility functions ---

    def _video_labels(self, width: int, height: int) -> tuple[str, str]:
        """Generate resolution and format labels based on dimensions."""
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
        """Clean text by stripping whitespace and handling None."""
        if value is None:
            return ""
        return value.strip()

    def _to_int(self, value: str | None, default: int = 0) -> int:
        """Convert string to integer with safe fallback."""
        try:
            if value is None:
                return default
            stripped = value.strip()
            return int(stripped)
        except TypeError, ValueError:
            return default

    def _to_float(self, value: str | None, default: float = 0.0) -> float:
        """Convert string to float with safe fallback."""
        try:
            if value is None:
                return default
            stripped = value.strip()
            return float(stripped)
        except TypeError, ValueError:
            return default
