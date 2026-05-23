from src.utils.log_util import LogUtil


class StrUtil:

    def __init__(self, log_util:LogUtil):
        super().__init__()
        self.log_util = log_util
        self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def join_strings(self, values: list) -> str:
        """
        Join non-empty values into a comma-separated string.

        Args:
            values: Sequence of values to join

        Returns:
            Comma-separated string of string representations of non-empty values
        """
        filtered = [str(value) for value in values if not self.is_empty_value(value)]
        return ", ".join(filtered)

    def is_empty_value(self, value) -> bool:
        """
        Check if a value is considered empty.

        Empty values are: None, empty strings, empty collections (list/tuple/set),
        empty dicts, and numeric zero values.

        Args:
            value: The value to check

        Returns:
            True if the value is considered empty, False otherwise
        """
        if value is None:
            return True

        if isinstance(value, str):
            return value.strip() == ""

        if isinstance(value, (int, float)):
            return value == 0

        if isinstance(value, (list, tuple, set)):
            if len(value) == 0:
                return True
            return all(self.is_empty_value(item) for item in value)

        if isinstance(value, dict):
            if len(value) == 0:
                return True
            return all(self.is_empty_value(item) for item in value.values())

        return False

    def pretty_label(self, key: str) -> str:
        """
        Convert a snake_case key to a human-readable label.

        Replaces underscores with spaces and converts to title case.

        Args:
            key: The string to format (typically a snake_case identifier)

        Returns:
            Formatted string in title case
        """
        return key.replace("_", " ").strip().title()
