class StrUtil:

    def __init__(self, log_util=None):
        super().__init__()
        self.log_util = log_util
        if self.log_util:
            self.log_util.debug(f"__init__ {self.__class__.__name__}")

    def join_strings(self, values: list) -> str:
        filtered = [str(value) for value in values if not self.is_empty_value(value)]
        return ", ".join(filtered)

    def is_empty_value(self, value) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        if isinstance(value, (list, tuple, set)):
            if len(value) == 0:
                return True
            return all(self.is_empty_value(item) for item in value)
        if isinstance(value, dict):
            if len(value) == 0:
                return True
            return all(self.is_empty_value(item) for item in value.values())
        if isinstance(value, (int, float)):
            return value == 0
        return False

    def pretty_label(self, key: str) -> str:
        return key.replace("_", " ").strip().title()
