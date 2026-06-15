# Project AI Context: MyVideoExplorer

## Overview
MyVideoExplorer is a PySide6 desktop application for browsing and managing video collections.

## Architecture
- **Dependency Management**: Uses an `AppContainer` for centralized object creation and dependency injection.
- **Entry Point**: `src/main.py` initializes the `AppContainer` and starts the `App`.
- **UI Structure**:
  - `src/app/app.py` constructs the `QMainWindow`.
  - Layout is based on `QSplitter` dividing left (navigation/folders) and right (content/details) panels.
- **State Management**: A `Controller` (accessible via container) manages high-level state, such as the current root folder(s).
- **Core Modules**:
  - `src/folder_...`: Navigation and folder management.
  - `src/file_list/`, `src/image_list/`: Browsing content.
  - `src/media_info...`: Displaying and managing media details/metadata.
  - `src/video_player/`: Video playback.
  - `src/settings/`: Application settings.
  - `src/theme/`: UI theming.
  - `src/utils/`: Utility functions.

## Development Guidelines
- Follow existing file structure and naming conventions.
- Use `AppContainer` to access application services/components.
- Keep UI components self-contained where possible.
