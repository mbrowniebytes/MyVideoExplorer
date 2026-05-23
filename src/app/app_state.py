from dataclasses import dataclass


@dataclass
class AppState:
    current_folder: str = ""
    current_file: str = ""
    current_image: str = ""
    current_tab: int = 0
    root_folder: str = ""
    root_folders: list[str] = None

    def __post_init__(self) -> None:
        if self.root_folders is None:
            self.root_folders = []
