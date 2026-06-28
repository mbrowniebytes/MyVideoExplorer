from dataclasses import dataclass, field


@dataclass
class AppState:
    prior_folder: str = ""
    current_folder: str = ""
    current_file: str = ""
    current_image: str = ""
    current_tab: int = 0
    root_folder: str = ""
    root_folders: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.root_folders:
            self.root_folders = []
