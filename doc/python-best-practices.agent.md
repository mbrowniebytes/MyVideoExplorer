# Python AI Development Best Practices: MyVideoExplorer

> **CRITICAL RULE**: NEVER run `git add` or `git commit`.

## 1. Code Structure & Organization
- **Feature Layout**: Code lives under `src/MyVideoExplorer/<feature>/`.
- **One Class Per File**: Keep classes in dedicated modules (e.g., `DbFilter` in `db_filter.py`, `FileUtilModel` in `file_util_model.py`).
- **Naming Conventions**:
  - Modules: `snake_case.py`
  - Classes: `PascalCase`
  - Functions & methods: `snake_case()`
  - Constants: `UPPER_SNAKE_CASE`
- **Imports Structure**:
  - Always start files with `from __future__ import annotations`.
  - Group imports: 1) Standard library, 2) Third-party (PySide6, DuckDB), 3) Local `MyVideoExplorer.*`.
  - Top-of-file only; never use inline or conditional imports.

```python
from __future__ import annotations

# Standard library
from pathlib import Path
from typing import Any

# Third-party
import duckdb
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

# Local imports
from MyVideoExplorer.app.app_signals import AppSignals
from MyVideoExplorer.utils.file_util_model import FileUtilModel
```

## 2. Typing & Python 3.14 Standards
- **Modern Collections**: Use standard built-in generics (`list[str]`, `dict[str, Any]`, `tuple[int, ...]`) instead of `typing.List` or `typing.Dict`.
- **Function Signatures**: Always supply complete type annotations for arguments and return types.
- **Ruff Compliance**: Line length is 88 characters. Follow idiomatic Python enforced by Ruff (`PTH`, `SIM`, `RET`, `FURB`).

## 3. PySide6 / Qt Best Practices
- **Decoupled Widgets**: UI components must remain self-contained. Never directly manipulate peer widgets; route events via `AppSignals` or notify `AppController`.
- **Non-Blocking GUI (Threading)**:
  - NEVER execute heavy I/O, directory scans, DuckDB queries, or image/video processing on the main Qt thread.
  - Offload long-running tasks to worker threads (`QThread` or background workers) and communicate status/results back via signals.
- **Memory & Object Lifecycle**: Always supply parent `QWidget` to child widgets and layouts to let Qt manage memory automatically.

## 4. DuckDB & Data Layer
- **Parameterized Queries**: Always use query parameter placeholders (`?`) with parameter sequences. Never interpolate raw values into SQL strings.
- **Path Normalization**: Store and compare filesystem paths using normalized forward slashes (`Path.as_posix()` and `.casefold()` for case-insensitive matching).
- **Vectorized Operations**: Leverage DuckDB's native array/list features for multiple tags or genres.

## 5. Filesystem & Resources
- **Pathlib**: Use `pathlib.Path` instead of `os.path` across all modules.
- **Bundled Resources**: For application assets, use `FileUtil.get_resource_path()` to ensure compatibility both in development and PyInstaller standalone builds (`sys._MEIPASS`).

## 6. Testing Strategy
- **Framework**: `pytest` with `pytest-qt` and `pytest-asyncio`.
- **Mirror Layout**: Tests live under `test/` mirroring the `src/MyVideoExplorer/` structure (e.g., `test/db/test_db_filter.py`).
- **Test Naming**: Use descriptive behavior names: `test_{functionality}_{condition}_should_{expected_result}` (or clear functional titles).
- **Qt Test Safety**: Initialize `QApplication.instance() or QApplication([])` or use `qtbot` fixtures in UI tests.
- **Headless Execution**: Use `$env:QT_QPA_PLATFORM = "offscreen"` in headless/CI environments.
- **Isolation**: Use pytest's `tmp_path` fixture for temporary file and database operations.

## 7. Quality & Verification Commands
- **Lint**: `ruff check --fix`
- **Format**: `ruff format`
- **Type Check**: `ty check`
- **Test**: `pytest`
- **Full Local CI**: `powershell -File ci.ps1` or `bash ci.sh`

## 8. Documentation & Comments
- **Docstrings**: Follow Google style for class and method docstrings.
- **Comments**: Explain *why* a particular approach was taken, not *what* the syntax does.


