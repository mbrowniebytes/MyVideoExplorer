# Project AI Context: MyVideoExplorer

## Overview
MyVideoExplorer is a PySide6 desktop application for browsing and managing video collections.

## Core Commands
- **Activate Env**: `source .venv/Scripts/activate`
- **Run Tests**: `pytest`
- **Linter**: `ruff check`
- **Build**: `pyinstaller --noconfirm main.spec`

## Architecture
- **Dependency Management**: Uses an `AppContainer` for centralized object creation and dependency injection.
- **Entry Point**: `src/MyVideoExplorer/main.py` initializes the `AppContainer` and starts the `App`.
- **UI Structure**:
  - `src/MyVideoExplorer/app/app.py` constructs the `QMainWindow`.
  - Layout is based on `QSplitter` dividing left (navigation/folders) and right (content/details) panels.
- **State Management**: A `Controller` (accessible via container) manages high-level state, such as the current root folder(s).
- **Core Modules**:
  - `src/MyVideoExplorer/folder_...`: Navigation and folder management.
  - `src/MyVideoExplorer/file_list/`, `src/image_list/`: Browsing content.
  - `src/MyVideoExplorer/media_info...`: Displaying and managing media details/metadata.
  - `src/MyVideoExplorer/video_player/`: Video playback.
  - `src/MyVideoExplorer/settings/`: Application settings.
  - `src/MyVideoExplorer/theme/`: UI theming.
  - `src/MyVideoExplorer/utils/`: Utility functions.

## Development Guidelines
- Follow existing file structure and naming conventions.
- Keep UI components self-contained where possible.
- Use the `doc/python-best-practices.md` doc for Python-specific development rules.
- Read `README.md` and `doc/development.md` for more details.
