# AI Context: MyVideoExplorer

> **CRITICAL RULE**: NEVER run `git add` or `git commit`.

## Quick Reference
- **Stack**: Python 3.14 | PySide6 6.11 | DuckDB | pytest-qt | ruff | ty
- **Run App**: `python -m MyVideoExplorer`
- **Run Tests**: `pytest` (mirrors `src/` in `test/`) | Headless: `$env:QT_QPA_PLATFORM='offscreen'; pytest`
- **Lint & Format**: `ruff check --fix` && `ruff format`
- **Type Check**: `ty check`

## Architecture
- **DI & Lifecycle**: `AppContainer` (`src/MyVideoExplorer/app/app_container.py`) creates and injects dependencies/singletons.
- **Entry Flow**: `src/MyVideoExplorer/main.py` -> `app/app_main.py` -> wires `AppContainer` -> launches `MainWindow` (`app/app.py`).
- **State & Signals**: `AppController` manages high-level state (selected folder/root). `AppSignals` (`app/app_signals.py`) routes cross-module Qt signals.
- **UI Layout (`QSplitter`)**:
  - **Left**: Folder navigation & filtering (`folder_nav`, `folder_list`, `folder_filter`).
  - **Right** (`media_info_tabs`): Tabbed workspace:
    - *media*: Content browsing via `file_list` (table) or `image_list` (grid/posters).
    - *info*: Metadata & `movie.nfo` details (`media_info*`, `tag_cloud`).
    - *settings*: Application preferences (`settings`).
- **Data & Scanning**: `db/` uses DuckDB for media cataloging, metadata caching, and search filtering.

## Key Modules (`src/MyVideoExplorer/`)
- `app/`: DI container, controller, signal bus, main window.
- `db/`: DuckDB schemas, repositories, file scanner & query filters.
- `file_list/`, `image_list/`: Table and thumbnail/poster grid views.
- `folder_list/`, `folder_nav/`, `folder_filter/`: Folder tree, breadcrumbs, search filtering.
- `media_info*/`: Metadata panels, sections, sidebars, and tab manager.
- `tag_cloud/`: Tag generation, browsing, and filtering widget.
- `video_player/`: Video playback integration.
- `settings/`: Configuration persistence and UI dialogs.
- `theme/`: Styling, palettes, QSS stylesheets.
- `utils/`: Path, file, datetime, platform helpers.
- `widgets/`: Reusable custom Qt components.

## AI Guidelines & Conventions
- **One class per file**: Snake_case filename, PascalCase class name. Keep classes in dedicated modules.
- **Imports**: Top-of-file only; no conditional imports; enforce `from __future__ import annotations`.
- **Paths**: Use `pathlib` for path operations and `utils/file_utils.py` for shared normalization. Keep application, filesystem, UI, and database path strings POSIX-formatted with `/` separators, including on Windows.
- **Threading**: Run long-running tasks (DB scan/filter, thumbnail gen) off the GUI thread with progress/cancellation.
- **Decoupling**: Keep UI widgets self-contained; communicate via `AppSignals` or `AppController`.
- **Test Naming**: `test_{func}_{condition}_should_{expected}`.
- **Docs**: Google-style docstrings (focus on *why*, not *what*).
- **References**: `doc/python-best-practices.agent.md` | `doc/development.md`.
