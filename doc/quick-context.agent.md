# Project AI Context: MyVideoExplorer
- Never run git add or git commit

## Overview

MyVideoExplorer is a PySide6 desktop application designed for browsing and managing video collections efficiently.

## Core Commands

- **Activate Env**: `source .venv/Scripts/activate`
- **Run Tests**: `pytest`
- **Linter**: `ruff check`
- **Build**: `pyinstaller --noconfirm main.spec`

## Architecture Highlights

- **Dependency Management**: Utilizes an `AppContainer` for centralized object creation and dependency injection.
- **Entry Point Initialization**: The application's startup is handled from `src/MyVideoExplorer/main.py`, initializing the `AppContainer`.
- **UI Structure**: Constructed in `src/MyVideoExplorer/app/app.py`, leveraging a `QSplitter` for layout division into left (navigation/folders) and right (content/details) panels.
- **State Management**: A `Controller` (accessible via container) manages high-level state, such as the current root
  folder(s).
- **Core Modules**:
    - `src/MyVideoExplorer/folder_...`: Navigation and folder management.
    - `src/MyVideoExplorer/file_list/`, `src/image_list/`: Browsing content.
    - `src/MyVideoExplorer/media_info...`: Displaying and managing media details/metadata.
    - `src/MyVideoExplorer/video_player/`: Video playback.
    - `src/MyVideoExplorer/settings/`: Application settings.
    - `src/MyVideoExplorer/theme/`: UI theming.
    - `src/MyVideoExplorer/utils/`: Utility functions.

## Development Guidelines
- Never run git add or git commit
- Adhere to existing file structure and naming conventions.
- Maintain UI components' self-containment where feasible.
- Reference Python best practices in `doc/python-best-practices.md`.
- Consult `README.md` and `doc/development.md` for additional development details.
