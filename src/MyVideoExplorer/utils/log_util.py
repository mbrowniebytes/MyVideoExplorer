
import datetime
import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from MyVideoExplorer.app.app_environment import IS_DEVELOPMENT

class CustomFormatter(logging.Formatter):
    """Custom formatter to match the previous structlog-based format."""
    def __init__(self, log_util: LogUtil) -> None:
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S")
        self.log_util = log_util

    def format(self, record: logging.LogRecord) -> str:
        record.asctime = self.formatTime(record, self.datefmt)
        level = record.levelname.upper()
        message = record.getMessage()

        caller = getattr(record, "caller", "n/a")
        extra_info = getattr(record, "extra_info", {})

        extra = f" - {extra_info}" if extra_info else ""

        return f"{record.asctime} - {level:<7} - {message} [{caller}]{extra}"

# Define log directory and file paths
BASE_PATH = Path().cwd().as_posix()
SRC_PATH = Path(BASE_PATH + "/MyVideoExplorer/")
LOG_DIR = Path("log")



class LogUtil:
    """Utility class for configuring and managing application logging."""

    # Map string levels to logging constants
    LEVEL_MAP: dict[str, int] = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        # "critical": logging.CRITICAL,
    }

    DEFAULT_LOG_LEVEL = "info"
    MAX_BACKUPS = 5
    ROTATION_PERIOD = "M" # "D"  # Daily rotation
    MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_FILE = LOG_DIR / "app.log"


    def __init__(self) -> None:
        """
        Initialize the LogUtil instance.

        Args:
            log_level: Optional initial log level (defaults to DEFAULT_LOG_LEVEL).
        """        """Create log directory and defaults split files if they don't exist."""
        if not LOG_DIR.exists():
            LOG_DIR.mkdir(parents=True)
        self.log_level = self.DEFAULT_LOG_LEVEL
        self._logger_initialized = False
        self._file_handler = RotatingFileHandler(self.LOG_FILE)

        # date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        # self.LOG_FILE = LOG_DIR / f"app-{date_str}.log"

    def get_log_level_value(self, level_str: str) -> int:
        """Convert a string log level name to its corresponding logging constant."""
        return self.LEVEL_MAP.get(level_str.lower(), logging.INFO)

    def ensure_log_level(self, level_str: str) -> str:
        """Convert a string log level name to its corresponding logging constant."""
        if self.LEVEL_MAP.get(level_str.lower()) is None:
            return "info"
        else:
            return level_str.lower()


    @property
    def logger_initialized(self) -> bool:
        """Check if the root logger has been initialized with file handler."""
        return self._logger_initialized

    def _ensure_log_directory(self) -> Path:
        """Create log directory if it doesn't exist."""
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        return LOG_DIR

    def _get_root_logger(self) -> logging.Logger:
        """Get the root logger instance."""
        return logging.getLogger()

    def _get_caller_info(self) -> str:
        """Extract file path (relative to MyVideoExplorer/) and line number from call stack."""
        # Get caller frame (skip this function and the convenience method)
        frames = traceback.extract_stack()

        if len(frames) <= 2:
            return "n/a"

        # Patterns to skip — anything outside MyVideoExplorer/ or in virtualenv
        skip_prefixes = [
            "MyVideoExplorer/utils/log_util.py",
            ".venv/",
            "site-packages/",
            "/usr/lib/python",
        ]

        app_frame = None
        for frame in reversed(frames):
            filename = frame.filename.replace("\\", "/")

            # Only accept frames that contain 'MyVideoExplorer/' — our application code
            if IS_DEVELOPMENT:
                if "MyVideoExplorer/" not in filename:
                    continue

            if any(p in filename for p in skip_prefixes):
                continue

            app_frame = frame
            break

        if app_frame is None:
            return "n/a"

        # Calculate relative path from app root, using Linux-style slashes
        full_path = str(app_frame.filename).replace("\\", "/")

        if full_path.find("MyVideoExplorer/") != -1:
            root_path = str(SRC_PATH)
        else:
            root_path = str(BASE_PATH)
        root_path = root_path.replace("\\", "/")
        rel_path = full_path.removeprefix(root_path) or "app"

        # Format as "filename@lineno"
        return f"{rel_path}@{app_frame.lineno}"

    def _custom_namer(self, default_name: str) -> str:
        # This will be called when doing the log rotation
        # default_name is app.log.YYYY-MM-DD
        # changes the name to app.YYYY-MM-DD.log
        base_filename, ext, date = default_name.split(".")
        return f"{base_filename}.{date}.{ext}"

    def configure(self, level_str: str) -> LogUtil:
        """
        Configure the root logger and file handler.

        Args:
            level_str: Optional log level string (defaults to instance's log_level).

        Returns:
            self for method chaining.
        """
        if self.logger_initialized:
            # Clear existing handlers on re-configuration
            logging.root.handlers.clear()

        # Get or use provided level
        self.log_level = self.ensure_log_level(level_str)
        effective_level = self.get_log_level_value(level_str or self.log_level)

        # Ensure log directory exists
        self._ensure_log_directory()

        # Configure file handler with daily rotation and backup limit

        # not working with custom date named log
        # self._file_handler = TimedRotatingFileHandler(
        #     self.LOG_FILE,
        #     when=self.ROTATION_PERIOD,
        #     interval=1,
        #     backupCount=self.MAX_BACKUPS,
        #     encoding="utf-8",
        #     utc=False,
        #     delay=True, # required else perms/timing issue
        # )
        # max size + custom cleanup()
        self._file_handler = RotatingFileHandler(
            self.LOG_FILE,
            maxBytes=self.MAX_BYTES,
            backupCount=self.MAX_BACKUPS,
            encoding="utf-8",
            delay=True,  # required else perms/timing issue
        )

        formatter = CustomFormatter(self)

        self._file_handler.setFormatter(formatter)
        self._file_handler.setLevel(effective_level)
        self._file_handler.namer = self._custom_namer

        # Add file handler to root logger if not already present
        logging.root.addHandler(self._file_handler)
        logging.root.setLevel(effective_level)

        self._logger_initialized = True

        return self

    def get_file_handler(self) -> RotatingFileHandler | None:
        """Return the current file handler or None."""
        return self._file_handler

    def _get_memory_usage(self) -> float:
        # Primary method: psutil (works reliably on Windows, macOS, Linux)
        try:
            # type: ignore[import-untyped]
            import psutil

            process = psutil.Process()
            mem_bytes = process.memory_info().rss
            return float(mem_bytes) / (1024 * 1024)
        except Exception as e:
            self.error(f"psutil memory measurement failed: {e}")

        # Final fallback: return 0 MB if all methods fail
        return 0.0

    def log_memory(self, message: str = "Memory usage") -> None:
        """
        Log current memory usage using os._exit_memory_usage().
        """
        mem_mb = self._get_memory_usage()
        self.info(f"{message} - {mem_mb:.2f} MB")

    def log_message(
        self,
        level: str = "info",
        message: str = "",
        *,
        extra_info: dict[str, Any] | None = None,
    ) -> None:
        """
        Log a formatted message using the configured file handler.

        Args:
            level: String log level (debug, info, warning, error, critical).
            message: The log message to write.
            extra_info: Optional dictionary of additional structured fields.
        """

        logger = logging.getLogger()
        log_method = getattr(logger, level.lower(), logger.info)
        extra = {"caller": self._get_caller_info()}
        if extra_info:
            extra["extra_info"] = extra_info
        log_method(message, extra=extra)

    # Helper convenience methods for common use cases
    def debug(
        self, message: str, *, extra_info: dict[str, Any] | None = None
    ) -> None:
        """Convenience method to log a DEBUG level message."""
        self.log_message(level="debug", message=message, extra_info=extra_info)

    def info(
        self, message: str, *, extra_info: dict[str, Any] | None = None
    ) -> None:
        """Convenience method to log an INFO level message."""
        self.log_message(level="info", message=message, extra_info=extra_info)

    def warn(
        self, message: str, *, extra_info: dict[str, Any] | None = None
    ) -> None:
        """Convenience method to log a WARNING level message."""
        self.log_message(level="warning", message=message, extra_info=extra_info)

    def error(
        self, message: str, *, extra_info: dict[str, Any] | None = None
    ) -> None:
        """Convenience method to log an ERROR level message."""
        self.log_message(level="error", message=message, extra_info=extra_info)
        # Flush on error to ensure it's written to disk before a potential crash
        if self._file_handler:
            self._file_handler.flush()

    def get_active_handlers(self) -> list[logging.Handler]:
        """Return a list of active handlers on the root logger."""
        return self._get_root_logger().handlers

    def remove_file_handler(self) -> None:
        """Remove the file handler from the root logger (useful for cleanup)."""
        if self._file_handler and self._file_handler in self.get_active_handlers():
            self._get_root_logger().removeHandler(self._file_handler)
            self._file_handler = None

    def close(self) -> None:
        self.cleanup()

    def handle_exception(
        self, exc_type: type[BaseException], exc_value: BaseException, exc_traceback: Any
    ) -> None:
        """Global exception handler to be used with sys.excepthook."""
        if (issubclass(exc_type, KeyboardInterrupt) or
                not IS_DEVELOPMENT):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        try:
            self.error(
                "Uncaught exception",
                extra_info={
                    "exc_type": str(exc_type),
                    "exc_value": str(exc_value),
                },
            )
            # Also log traceback
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            # could be debug
            # log as error so have context with errors
            # traceback already prepends: Traceback (most recent call last):
            self.error(f"{tb_str}")
        except Exception as handler_exception:
            # If exception handling itself fails, write directly to file
            try:
                log_file = self.LOG_FILE
                log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"CRITICAL: Exception in exception handler: {handler_exception}\n")
                    f.write(f"Original exception: {exc_type.__name__}: {exc_value}\n")
                    f.write(traceback.format_exc())
                    f.write("\n")
            except Exception:
                pass  # Silently fail if we can't log
        finally:
            # Always flush to ensure data is written
            if self._file_handler:
                try:
                    self._file_handler.flush()
                except Exception:
                    pass

    def cleanup(self) -> None:
        """Manage daily backups of a file, keeping up to max_backups."""

        log_dir = LOG_DIR

        # Keep only the max_backups most recent backups
        # explicit set, since deleting files
        pattern = "app*log"
        backups = sorted(log_dir.glob(pattern), reverse=True, key=os.path.getmtime)

        for old_backup in backups[self.MAX_BACKUPS:]:
            try:
                # print(f"cleanup: old_backup.unlink {old_backup}")
                old_backup.unlink()
            except OSError as e:
                self.warn(f"Failed to delete old backup {old_backup}: {e}")

        """Close all handlers associated with this LogUtil instance."""
        if self._file_handler:
            self._file_handler.close()
        self.remove_file_handler()

        # date_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        backup_log = LOG_DIR / f"app-{date_str}.log"
        # shutil.move(self.LOG_FILE, LOG_DIR / f"app-{date_str}.log")
        self.concat_files([self.LOG_FILE.as_posix()], backup_log.as_posix())

        # self.LOG_FILE.unlink()
        open(self.LOG_FILE, "w").close()

    def concat_files(self, source_files: list[str], destination_file: str) -> None:
        with open(destination_file, 'a') as dest:
            for filename in source_files:
                with open(filename) as src:
                    content = src.read()
                    dest.write(content)
                    if not content.endswith('\n'):
                        dest.write('\n')


