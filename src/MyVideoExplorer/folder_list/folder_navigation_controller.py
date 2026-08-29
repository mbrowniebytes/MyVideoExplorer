import random

class FolderNavigationController:
    HISTORY_FOLDER_LENGTH = 100

    def __init__(self):
        self._folder_history: list[str] = []
        self._current_history_index = -1

    def add_to_history(self, folder_path: str):
        if self._folder_history and self._folder_history[self._current_history_index] == folder_path:
            return

        # Truncate forward history if we are in the middle
        if self._current_history_index < len(self._folder_history) - 1:
            self._folder_history = self._folder_history[: self._current_history_index + 1]

        self._folder_history.append(folder_path)
        self._current_history_index = len(self._folder_history) - 1

        if len(self._folder_history) > self.HISTORY_FOLDER_LENGTH:
            self._folder_history.pop(0)
            self._current_history_index -= 1

    def get_backward_folder(self) -> str | None:
        if self._current_history_index > 0:
            self._current_history_index -= 1
            return self._folder_history[self._current_history_index]
        return None

    def get_forward_folder(self) -> str | None:
        if self._current_history_index < len(self._folder_history) - 1:
            self._current_history_index += 1
            return self._folder_history[self._current_history_index]
        return None

    def select_random_folder(self, valid_folders: list[str]) -> str | None:
        if valid_folders:
            return random.choice(valid_folders)
        return None

    def can_go_backward(self) -> bool:
        return self._current_history_index > 0

    def can_go_forward(self) -> bool:
        return self._current_history_index < len(self._folder_history) - 1
