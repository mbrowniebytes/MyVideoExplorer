import re
import shutil
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from MyVideoExplorer.app.app_signals_model import SignalFlow, SignalPayload
from MyVideoExplorer.db.db_filters import DEFAULT_FILTER_DB_PATH, DbFilters
from MyVideoExplorer.theme.theme import APP_THEME
from MyVideoExplorer.utils.file_util import FileUtils
from MyVideoExplorer.utils.json_util import JsonUtil

# Use a package-local defaults directory so built-in defaults are versioned with
# the application instead of living only at the repo root. Runtime user settings
# still live in the working-directory cfg folder for easy local editing.
PACKAGE_CFG_DIR = Path(__file__).resolve().parent / "cfg"
CFG_DIR = Path("cfg")
SETTINGS_STATE_FILE = CFG_DIR / "settings_state.json"
SETTINGS_APP_FILE = CFG_DIR / "settings_app.json"
SETTINGS_PLAYER_FILE = CFG_DIR / "settings_player.json"
SETTINGS_UI_FILE = CFG_DIR / "settings_ui.json"
SETTINGS_MEDIA_FILE = CFG_DIR / "settings_media.json"
SETTINGS_FILTER_FILE = CFG_DIR / "settings_filter.json"

DEFAULTS_STATE_FILE = PACKAGE_CFG_DIR / "defaults_state.json"
DEFAULTS_APP_FILE = PACKAGE_CFG_DIR / "defaults_app.json"
DEFAULTS_PLAYER_FILE = PACKAGE_CFG_DIR / "defaults_player.json"
DEFAULTS_UI_FILE = PACKAGE_CFG_DIR / "defaults_ui.json"
DEFAULTS_MEDIA_FILE = PACKAGE_CFG_DIR / "defaults_media.json"
DEFAULTS_FILTER_FILE = PACKAGE_CFG_DIR / "defaults_filter.json"
SCAN_MEDIA_TIMEOUT_OPTIONS = (30, 60, 120, 300, 600)
DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS = 120

VIDEO_PLAYER_DEFAULTS: tuple[tuple[str, str, bool], ...] = (
    ("os_default", "OS default", True),
    ("vlc", "VLC", False),
    ("potplayer", "PotPlayer", False),
    ("mpc_qt", "MPC-QT", False),
    ("custom", "Custom", False),
)


class SettingsState(QObject):
    settings_changed = Signal(object)
    window_size_changed = Signal(object)
    window_pos_changed = Signal(object)
    tags_changed = Signal()
    tag_counts_changed = Signal()
    filter_counts_changed = Signal()
    media_folder_selection_changed = Signal(object)

    def __init__(self, log_util: Any, filter_db_path: Path | str | None = None) -> None:
        super().__init__()

        self.log_util = log_util
        self.json_util = JsonUtil(self.log_util)

        self.prior_folder = ""
        self.app_pos = ""
        self.app_size = ""

        self.auto_select_folder = "auto_select_prior_folder"
        self.log_level = "info"
        self.launch_app_size = "app_size_min"
        self.launch_app_pos = "app_pos_center_center"
        self.show_loading_screen = True
        self.scan_media_timeout_seconds = DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
        self.nfo_collapsed_by_default = False
        self.meta_collapsed_by_default = False
        self.video_player_configs = self._default_video_player_configs()

        self.media_configs: list[dict[str, Any]] = []
        self.selected_media_folders: list[str] = []
        self.tags: list[dict[str, str]] = []
        self._db_enabled = True
        self.saved_filters: list[dict[str, Any]] = []
        self._load_settings()
        self.filter_store = DbFilters(
            self,
            self.saved_filters,
            db_path=filter_db_path or DEFAULT_FILTER_DB_PATH,
        )
        self.saved_filters = self.filter_store.list_filters()
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def _ensure_defaults(self) -> None:
        """Create user settings dir and package defaults if they don't exist."""
        if not CFG_DIR.exists():
            CFG_DIR.mkdir(parents=True)
        PACKAGE_CFG_DIR.mkdir(parents=True, exist_ok=True)

        state_defaults: dict[str, str] = {
            "prior_folder": "",
            "app_pos": "",
            "app_size": "",
        }
        app_defaults: dict[str, Any] = {
            "log_level": self.log_level,
            "auto_select_folder": self.auto_select_folder,
            "launch_app_size": self.launch_app_size,
            "launch_app_pos": self.launch_app_pos,
            "show_loading_screen": self.show_loading_screen,
            "scan_media_timeout_seconds": self.scan_media_timeout_seconds,
            "nfo_collapsed_by_default": self.nfo_collapsed_by_default,
            "meta_collapsed_by_default": self.meta_collapsed_by_default,
        }
        ui_defaults: dict[str, int | str] = {
            "font_size": 18,
            "app_font": "Lato",
            "indent_indicator": "・",
        }
        media_defaults: dict[str, Any] = {
            "media_configs": self.media_configs,
            "db_enabled": self._db_enabled,
        }
        filter_defaults: dict[str, list[dict[str, Any]]] = {
            "saved_filters": self.saved_filters,
        }

        self.json_util.ensure_defaults(
            PACKAGE_CFG_DIR, DEFAULTS_STATE_FILE, state_defaults
        )
        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_APP_FILE, app_defaults)
        player_defaults = {"video_player_configs": self.video_player_configs}
        self.json_util.ensure_defaults(
            PACKAGE_CFG_DIR, DEFAULTS_PLAYER_FILE, player_defaults
        )
        self.json_util.ensure_defaults(PACKAGE_CFG_DIR, DEFAULTS_UI_FILE, ui_defaults)
        self.json_util.ensure_defaults(
            PACKAGE_CFG_DIR, DEFAULTS_MEDIA_FILE, media_defaults
        )
        self.json_util.ensure_defaults(
            PACKAGE_CFG_DIR, DEFAULTS_FILTER_FILE, filter_defaults
        )

        if not SETTINGS_APP_FILE.exists() and DEFAULTS_APP_FILE.exists():
            try:
                CFG_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(DEFAULTS_APP_FILE, SETTINGS_APP_FILE)
            except OSError as e:
                self.log_util.error(
                    f"Failed to create {SETTINGS_APP_FILE} from {DEFAULTS_APP_FILE}: {e}"
                )

    def _load_settings(self) -> None:
        """Load settings from split json files, falling back to split defaults."""
        self._ensure_defaults()

        # Load State Settings
        state_data = self.json_util.load_json(DEFAULTS_STATE_FILE)
        if SETTINGS_STATE_FILE.exists():
            state_data.update(self.json_util.load_json(SETTINGS_STATE_FILE))

        self.prior_folder = FileUtils.normalize_path(state_data.get("prior_folder", ""))
        self.app_size = state_data.get("app_size", "")
        self.app_pos = state_data.get("app_pos", "")

        # Load App Settings
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        if SETTINGS_APP_FILE.exists():
            app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))

        self.log_level = app_data.get("log_level", self.log_level)
        self.auto_select_folder = app_data.get(
            "auto_select_folder", "auto_select_prior_folder"
        )
        self.launch_app_size = app_data.get("launch_app_size", "app_size_min")
        self.launch_app_pos = app_data.get("launch_app_pos", "app_pos_center_center")
        self.show_loading_screen = app_data.get("show_loading_screen", True)
        self.scan_media_timeout_seconds = self._validated_scan_media_timeout(
            app_data.get(
                "scan_media_timeout_seconds", DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
            )
        )
        self.nfo_collapsed_by_default = app_data.get("nfo_collapsed_by_default", False)
        self.meta_collapsed_by_default = app_data.get(
            "meta_collapsed_by_default", False
        )
        self._load_player_settings(app_data)

        # Load UI Settings
        ui_data = self.json_util.load_json(DEFAULTS_UI_FILE)
        if SETTINGS_UI_FILE.exists():
            ui_data.update(self.json_util.load_json(SETTINGS_UI_FILE))

        APP_THEME.font_size = ui_data.get("font_size", APP_THEME.font_size)
        APP_THEME.font_family = ui_data.get("app_font", APP_THEME.font_family)
        APP_THEME.indent_indicator = ui_data.get(
            "indent_indicator", APP_THEME.indent_indicator
        )

        # Load Media Settings
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        if SETTINGS_MEDIA_FILE.exists():
            media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.media_configs = media_data.get("media_configs", self.media_configs)
        self._normalize_media_config_paths()
        self._db_enabled = media_data.get("db_enabled", False)

        # Ensure each folder config has an icon
        for config in self.media_configs:
            if "icon" not in config:
                config["icon"] = "fa6s.folder"

        # Load Filter Settings
        filter_data = self.json_util.load_json(DEFAULTS_FILTER_FILE)
        if SETTINGS_FILTER_FILE.exists():
            filter_data.update(self.json_util.load_json(SETTINGS_FILTER_FILE))
        self.saved_filters = filter_data.get("saved_filters", self.saved_filters)

        # Migration: if saved_filters is a dict, convert it to a list of dicts
        if isinstance(self.saved_filters, dict):
            new_filters: list[dict[str, Any]] = []
            for name, filters in self.saved_filters.items():
                new_filters.append({"name": name, "filters": filters})
            self.saved_filters = new_filters

    def save_state(self, settings: dict[str, str]) -> None:
        """Save only App tab settings."""
        self._ensure_defaults()

        state_settings: dict[str, str] = {
            "prior_folder": FileUtils.normalize_path(settings.get("prior_folder", "")),
            "app_size": settings.get("app_size", ""),
            "app_pos": settings.get("app_pos", ""),
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_STATE_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_STATE_FILE, state_settings)

    def save_app(self) -> None:
        """Save only App tab settings."""
        self._ensure_defaults()

        app_settings: dict[str, Any] = {
            "log_level": self.log_level,
            "auto_select_folder": self.auto_select_folder,
            "launch_app_size": self.launch_app_size,
            "launch_app_pos": self.launch_app_pos,
            "show_loading_screen": self.show_loading_screen,
            "scan_media_timeout_seconds": self.scan_media_timeout_seconds,
            "nfo_collapsed_by_default": self.nfo_collapsed_by_default,
            "meta_collapsed_by_default": self.meta_collapsed_by_default,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_APP_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_APP_FILE, app_settings)

    def save_player(self) -> None:
        """Persist configured video-player settings separately from app settings."""
        self._ensure_defaults()
        self.json_util.backup_file(SETTINGS_PLAYER_FILE, max_backups=5)
        self.json_util.save_json(
            SETTINGS_PLAYER_FILE,
            {"video_player_configs": self.video_player_configs},
        )

    def save_ui(self) -> None:
        """Persist UI settings to file."""
        self._ensure_defaults()

        settings_data = {
            "font_size": APP_THEME.font_size,
            "app_font": APP_THEME.font_family,
            "indent_indicator": APP_THEME.indent_indicator,
        }

        # Backup then save
        self.json_util.backup_file(SETTINGS_UI_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_UI_FILE, settings_data)

    def save_media(self) -> None:
        """Save only Media tab settings."""
        self._ensure_defaults()
        self._normalize_media_config_paths()

        media_settings: dict[str, Any] = {
            "media_configs": self.media_configs,
            "db_enabled": self._db_enabled,
        }

        self.log_util.info(f"Saving media_settings: {media_settings}")
        # Backup then save
        self.json_util.backup_file(SETTINGS_MEDIA_FILE, max_backups=5)
        self.json_util.save_json(SETTINGS_MEDIA_FILE, media_settings)

    def save_filters(self) -> None:
        """Persist the saved filters in the filter catalog database."""
        self._ensure_defaults()
        self.filter_store.replace_all(self.saved_filters)
        self.saved_filters = self.filter_store.list_filters()
        self._emit_filters_changed()

    def _emit_filters_changed(self) -> None:
        self.settings_changed.emit(
            SignalPayload(
                data=None,
                sender=self.__class__.__name__,
                name="Settings Changed",
                description="Filter settings were saved.",
                flow=SignalFlow.COMPONENT_INTERACTION,
            )
        )

    @staticmethod
    def is_valid_tag_name(tag: str) -> bool:
        """Check if a tag name matches the shared name validation pattern."""
        from MyVideoExplorer.tag_cloud.tag_util import VALID_NAME_PATTERN

        return bool(VALID_NAME_PATTERN.fullmatch(tag.strip()))

    @staticmethod
    def normalize_tags(tags: Any) -> list[dict[str, str]]:
        if not isinstance(tags, list):
            return []
        normalized: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in tags:
            if not isinstance(item, dict):
                continue
            tag = str(item.get("tag", "")).strip()
            if (
                not tag
                or not SettingsState.is_valid_tag_name(tag)
                or tag.casefold() in seen
            ):
                continue
            seen.add(tag.casefold())
            color = str(item.get("color", "#808080")).strip()
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                color = "#808080"
            normalized.append({"tag": tag, "color": color})
        return normalized

    def add_tag(self, tag: str, color: str = "#808080") -> bool:
        clean_tag = tag.strip()
        if (
            not clean_tag
            or not SettingsState.is_valid_tag_name(clean_tag)
            or any(item["tag"].casefold() == clean_tag.casefold() for item in self.tags)
        ):
            return False
        self.tags.append(self.normalize_tags([{"tag": clean_tag, "color": color}])[0])
        self.tags_changed.emit()
        return True

    def set_tags(self, tags: list[dict[str, str]]) -> None:
        self.tags = self.normalize_tags(tags)
        self.tags_changed.emit()

    def load_ui(self) -> None:
        """Reload UI settings from file."""
        ui_data = self.json_util.load_json(DEFAULTS_UI_FILE)
        if SETTINGS_UI_FILE.exists():
            ui_data.update(self.json_util.load_json(SETTINGS_UI_FILE))

        APP_THEME.font_size = ui_data.get("font_size", APP_THEME.font_size)
        APP_THEME.font_family = ui_data.get("app_font", APP_THEME.font_family)
        APP_THEME.indent_indicator = ui_data.get(
            "indent_indicator", APP_THEME.indent_indicator
        )

    def load_app(self) -> None:
        """Reload App settings from file."""
        if not SETTINGS_APP_FILE.exists() and DEFAULTS_APP_FILE.exists():
            try:
                CFG_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(DEFAULTS_APP_FILE, SETTINGS_APP_FILE)
            except OSError as e:
                self.log_util.error(
                    f"Failed to create {SETTINGS_APP_FILE} from {DEFAULTS_APP_FILE}: {e}"
                )
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        if SETTINGS_APP_FILE.exists():
            app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))
        self.log_level = app_data.get("log_level", self.log_level)
        self.auto_select_folder = app_data.get(
            "auto_select_folder", "auto_select_prior_folder"
        )
        self.launch_app_size = app_data.get("launch_app_size", "app_size_min")
        self.launch_app_pos = app_data.get("launch_app_pos", "app_pos_last")
        self.show_loading_screen = app_data.get("show_loading_screen", True)
        self.scan_media_timeout_seconds = self._validated_scan_media_timeout(
            app_data.get(
                "scan_media_timeout_seconds", DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
            )
        )
        self.nfo_collapsed_by_default = app_data.get("nfo_collapsed_by_default", False)
        self.meta_collapsed_by_default = app_data.get(
            "meta_collapsed_by_default", False
        )

    def load_player(self) -> None:
        """Reload configured video players from their settings file."""
        self._ensure_defaults()
        app_data = self.json_util.load_json(DEFAULTS_APP_FILE)
        if SETTINGS_APP_FILE.exists():
            app_data.update(self.json_util.load_json(SETTINGS_APP_FILE))
        self._load_player_settings(app_data)

    def _load_player_settings(self, legacy_app_data: dict[str, Any]) -> None:
        player_data = self.json_util.load_json(DEFAULTS_PLAYER_FILE)
        if SETTINGS_PLAYER_FILE.exists():
            player_data.update(self.json_util.load_json(SETTINGS_PLAYER_FILE))
        legacy_configs = legacy_app_data.get("video_player_configs")
        if not SETTINGS_PLAYER_FILE.exists() and legacy_configs is not None:
            player_data["video_player_configs"] = legacy_configs
        self.video_player_configs = self._normalize_video_player_configs(
            player_data.get("video_player_configs")
        )

    @staticmethod
    def _default_video_player_configs() -> list[dict[str, Any]]:
        return [
            {
                "id": player_id,
                "label": label,
                "executable": {
                    "vlc": "C:/Program Files/VideoLAN/VLC/vlc.exe",
                    "potplayer": "C:/Program Files/DAUM/PotPlayer/PotPlayerMini64.exe",
                    "mpc_qt": "C:/Program Files/MPC-QT/mpc-qt.exe",
                }.get(player_id, ""),
                "arguments": "",
                "is_default": is_default,
                "show_icon": is_default,
            }
            for player_id, label, is_default in VIDEO_PLAYER_DEFAULTS
        ]

    @classmethod
    def _normalize_video_player_configs(cls, value: Any) -> list[dict[str, Any]]:
        stored = (
            {
                entry.get("id"): entry
                for entry in value
                if isinstance(entry, dict) and isinstance(entry.get("id"), str)
            }
            if isinstance(value, list)
            else {}
        )
        selected_id = next(
            (
                entry["id"]
                for entry in (value if isinstance(value, list) else [])
                if isinstance(entry, dict)
                and isinstance(entry.get("id"), str)
                and entry.get("is_default") is True
            ),
            None,
        )
        configs = cls._default_video_player_configs()
        for config in configs:
            saved = stored.get(config["id"], {})
            executable = saved.get("executable", config["executable"])
            if isinstance(executable, str):
                config["executable"] = executable
            arguments = saved.get("arguments", config["arguments"])
            if isinstance(arguments, str):
                config["arguments"] = arguments
            config["show_icon"] = (
                True
                if config["id"] == "os_default"
                else bool(saved.get("show_icon", config["show_icon"]))
            )
            config["is_default"] = (
                config["id"] == selected_id
                if selected_id is not None
                else bool(saved.get("is_default", config["is_default"]))
            )
        if not any(config["is_default"] for config in configs):
            configs[0]["is_default"] = True
        return configs

    @staticmethod
    def _validated_scan_media_timeout(value: Any) -> int:
        try:
            timeout = int(value)
        except TypeError, ValueError:
            return DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
        return (
            timeout
            if timeout in SCAN_MEDIA_TIMEOUT_OPTIONS
            else DEFAULT_SCAN_MEDIA_TIMEOUT_SECONDS
        )

    def load_media(self) -> None:
        """Reload Media settings from file."""
        media_data = self.json_util.load_json(DEFAULTS_MEDIA_FILE)
        if SETTINGS_MEDIA_FILE.exists():
            media_data.update(self.json_util.load_json(SETTINGS_MEDIA_FILE))
        self.media_configs = media_data.get("media_configs", self.media_configs)
        self._normalize_media_config_paths()
        self.log_util.info(f"Loaded media_configs: {self.media_configs}")
        self._db_enabled = media_data.get("db_enabled", True)
        # Ensure each folder config has an icon
        for config in self.media_configs:
            if "icon" not in config:
                config["icon"] = "fa6s.folder"

    def _normalize_media_config_paths(self) -> None:
        for config in self.media_configs:
            if isinstance(config, dict) and config.get("path"):
                config["path"] = FileUtils.normalize_path(str(config["path"]))

    def load_filters(self) -> None:
        """Reload saved filters from the database-backed catalog."""
        self.saved_filters = self.filter_store.list_filters()

    def save_filter(
        self,
        name: str,
        filter_cfg: list[dict[str, Any]],
        original_name: str | None = None,
    ) -> None:
        """
        Saves a named filter configuration.

        Args:
            name: Filter name to store.
            filter_cfg: Filter criteria list.
            original_name: Previous name when renaming, so the existing entry is
                replaced in place instead of a duplicate being appended.
        """
        self.filter_store.save_filter(name, filter_cfg, original_name)
        self.saved_filters = self.filter_store.list_filters()
        self._emit_filters_changed()

    def delete_filter(self, name: str) -> None:
        """Delete a named filter configuration from the catalog."""
        self.filter_store.delete_filter(name)
        self.saved_filters = self.filter_store.list_filters()
        self._emit_filters_changed()

    @staticmethod
    def sanitize_media_label(label: Any) -> str:
        """Sanitize a media folder label for use in database file names.

        This method replaces characters that are invalid for file names
        (slashes, wildcards, etc.) and collapses whitespace. It does not
        enforce the shared name validation pattern — use validate_name()
        for that. The result is safe for constructing DB file paths.
        """
        text = str(label).strip()
        if not text:
            return ""
        text = re.sub(r"[\\/:*?\"<>|]", "_", text)
        text = re.sub(r"[^a-zA-Z0-9_.\-\s]", "_", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = text.strip(" ._-")
        return text

    @staticmethod
    def validate_media_label(label: str) -> tuple[bool, str]:
        """Validate a media folder label using the shared name validation.

        Args:
            label: The media folder label to validate.

        Returns:
            A tuple of (is_valid, error_message). If valid, error_message is empty.
        """
        from MyVideoExplorer.tag_cloud.tag_util import validate_name

        return validate_name(label)

    def get_db_path(
        self, folder_config: dict[str, Any], label_override: str | None = None
    ) -> str:
        label = self.sanitize_media_label(
            label_override
            if label_override is not None
            else folder_config.get("label", "media")
        )
        if not label:
            label = "media"
        if label in {".", ".."}:
            label = "media"
        # Store DB path using POSIX separator to keep file naming consistent across platforms
        return f"db/media_{label}.db"

    def validate_media_configs(self, media_configs: list[dict[str, Any]]) -> list[str]:
        errors: list[str] = []
        seen_names: set[str] = set()
        seen_paths: set[str] = set()

        for idx, config in enumerate(media_configs, start=1):
            label = str(config.get("label", "")).strip()
            path = str(config.get("path", "")).strip()
            safe_label = self.sanitize_media_label(label)

            # Validate label characters using shared validation
            if label:
                is_valid, error_msg = self.validate_media_label(label)
                if not is_valid:
                    errors.append(
                        f"Media config '{label}' has an invalid name. {error_msg}"
                    )

            if not label:
                errors.append(f"Media config #{idx} is missing a name.")
            elif not safe_label:
                errors.append(f"Media config #{idx} has an invalid name: '{label}'")

            if not path:
                errors.append(
                    f"Media config '{label or f'#{idx}'}' is missing a folder path."
                )
            else:
                # Validate path characters
                from MyVideoExplorer.utils.file_util import validate_path

                is_valid_path, path_error = validate_path(path)
                if not is_valid_path:
                    errors.append(
                        f"Media config '{label or f'#{idx}'}' has an invalid path. {path_error}"
                    )
                elif not Path(path).is_dir():
                    errors.append(
                        f"Media config '{label or f'#{idx}'}' path does not exist: {path}"
                    )

            # Check for duplicate paths (normalized and case-insensitive on Windows)
            if path:
                normalized_path = FileUtils.normalize_path(path).casefold()
                if normalized_path in seen_paths:
                    errors.append(
                        f"Media folder path '{path}' is already registered. "
                        "Each path must be unique."
                    )
                seen_paths.add(normalized_path)

            if safe_label:
                normalized_name = safe_label.casefold()
                if normalized_name in seen_names:
                    errors.append(
                        f"Media names must be unique. '{safe_label}' is used more than once."
                    )
                seen_names.add(normalized_name)

        return errors

    def rename_db_for_media_config(self, media_config: dict[str, Any]) -> None:
        previous_label = str(media_config.get("_previous_label", "")).strip()
        current_label = str(media_config.get("label", "")).strip()
        if not previous_label or previous_label == current_label:
            return

        old_db = Path(self.get_db_path({"label": previous_label}, previous_label))
        new_db = Path(self.get_db_path({"label": current_label}, current_label))

        if old_db.resolve() == new_db.resolve():
            media_config["_previous_label"] = current_label
            return

        if new_db.exists() and not old_db.exists():
            raise ValueError(
                f"The database file '{new_db.name}' already exists. "
                "Please choose a unique media name."
            )

        if old_db.exists():
            try:
                old_db.replace(new_db)
            except OSError as exc:
                raise OSError(
                    f"Unable to rename database file from '{old_db.name}' to '{new_db.name}'. "
                    f"Original media name kept. Details: {exc}"
                ) from exc

        media_config["_previous_label"] = current_label

    def sync_db_file_names(self, media_configs: list[dict[str, Any]]) -> None:
        for config in media_configs:
            if not isinstance(config, dict):
                continue
            self.rename_db_for_media_config(config)

    def db_enabled(self) -> bool:
        # Check if the setting is 'Yes' (True)
        if not self._db_enabled:
            return False

        # Check if at least one DB exists
        for media_config in self.media_configs:
            db_path = self.get_db_path(media_config)
            if Path(db_path).exists():
                return True
        return False

    def save_settings(self) -> None:
        """Save all tabs' settings"""
        self.save_app()
        self.save_player()
        self.save_ui()
        self.save_media()
        self.save_filters()
