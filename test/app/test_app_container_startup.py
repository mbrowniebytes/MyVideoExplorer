from __future__ import annotations

import contextlib
import json
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

from MyVideoExplorer.app.app_container import AppContainer

_CONTAINER_PATCHES = [
    "MyVideoExplorer.app.app_container.FolderFilters",
    "MyVideoExplorer.app.app_container.FolderNav",
    "MyVideoExplorer.app.app_container.FolderList",
    "MyVideoExplorer.app.app_container.FileList",
    "MyVideoExplorer.app.app_container.MediaInfoView",
    "MyVideoExplorer.app.app_container.MediaInfoSideView",
    "MyVideoExplorer.app.app_container.MediaInfo",
    "MyVideoExplorer.app.app_container.ImageListView",
    "MyVideoExplorer.app.app_container.ImageList",
    "MyVideoExplorer.app.app_container.MediaInfoTabs",
]


@pytest.fixture
def mock_log():
    return MagicMock()


@pytest.fixture
def container_patches(mock_log):
    """Return an ExitStack with all container dependency patches applied (no Settings)."""
    with contextlib.ExitStack() as stack:
        stack.enter_context(
            patch(
                "MyVideoExplorer.utils.log_util.LogUtil.get_default",
                return_value=mock_log,
            )
        )
        mock_log.configure.return_value = mock_log
        for target in _CONTAINER_PATCHES:
            stack.enter_context(patch(target))
        yield stack, mock_log


def _make_container(container_patches):
    """Create a QMainWindow and AppContainer inside the patched context."""
    window = QMainWindow()
    container = AppContainer(window)
    return window, container


def test_app_container_creates_settings_app_from_defaults(
    tmp_path, monkeypatch, mock_log
):
    QApplication.instance() or QApplication([])

    cfg_dir = tmp_path / "cfg"
    defaults_app_file = tmp_path / "defaults_app.json"
    settings_app_file = cfg_dir / "settings_app.json"

    default_data = {
        "auto_select_folder": "auto_select_prior_folder",
        "launch_app_size": "app_size_1200x800",
        "launch_app_pos": "app_pos_center_center",
        "show_loading_screen": True,
        "log_level": "info",
    }
    defaults_app_file.write_text(json.dumps(default_data), encoding="utf-8")

    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.DEFAULTS_APP_FILE", defaults_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.SETTINGS_APP_FILE", settings_app_file
    )

    with contextlib.ExitStack() as stack:
        stack.enter_context(
            patch(
                "MyVideoExplorer.utils.log_util.LogUtil.get_default",
                return_value=mock_log,
            )
        )
        mock_log.configure.return_value = mock_log
        stack.enter_context(patch("MyVideoExplorer.app.app_container.Settings"))
        for target in _CONTAINER_PATCHES:
            stack.enter_context(patch(target))
        _, container = _make_container(stack)

    assert settings_app_file.exists()
    saved_data = json.loads(settings_app_file.read_text(encoding="utf-8"))
    assert saved_data == default_data
    assert container.log_util == mock_log
    # Ensure error was not called for missing configuration file
    for call in mock_log.error.call_args_list:
        assert "Failed to load" not in str(call)
        assert "Error loading configuration" not in str(call)


def test_app_container_preserves_existing_settings_app(tmp_path, monkeypatch, mock_log):
    QApplication.instance() or QApplication([])

    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    defaults_app_file = tmp_path / "defaults_app.json"
    settings_app_file = cfg_dir / "settings_app.json"

    default_data = {
        "log_level": "info",
    }
    defaults_app_file.write_text(json.dumps(default_data), encoding="utf-8")

    custom_data = {
        "log_level": "debug",
    }
    settings_app_file.write_text(json.dumps(custom_data), encoding="utf-8")

    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.DEFAULTS_APP_FILE", defaults_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.SETTINGS_APP_FILE", settings_app_file
    )

    with contextlib.ExitStack() as stack:
        stack.enter_context(
            patch(
                "MyVideoExplorer.utils.log_util.LogUtil.get_default",
                return_value=mock_log,
            )
        )
        mock_log.configure.return_value = mock_log
        stack.enter_context(patch("MyVideoExplorer.app.app_container.Settings"))
        for target in _CONTAINER_PATCHES:
            stack.enter_context(patch(target))
        _, _ = _make_container(stack)

    saved_data = json.loads(settings_app_file.read_text(encoding="utf-8"))
    assert saved_data["log_level"] == "debug"
    mock_log.configure.assert_called_with("debug")


def test_app_startup_and_initialization_applies_window_size_once(
    tmp_path, monkeypatch, container_patches
):
    QApplication.instance() or QApplication([])

    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    defaults_app_file = tmp_path / "defaults_app.json"
    settings_app_file = cfg_dir / "settings_app.json"

    default_data = {
        "launch_app_size": "app_size_1600x900",
        "launch_app_pos": "app_pos_center_center",
        "log_level": "info",
    }
    defaults_app_file.write_text(json.dumps(default_data), encoding="utf-8")
    settings_app_file.write_text(json.dumps(default_data), encoding="utf-8")

    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.DEFAULTS_APP_FILE", defaults_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.SETTINGS_APP_FILE", settings_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.DEFAULTS_APP_FILE", defaults_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.SETTINGS_APP_FILE", settings_app_file
    )
    monkeypatch.setattr("MyVideoExplorer.settings.settings_state.CFG_DIR", cfg_dir)

    _, mock_log = container_patches
    window, container = _make_container(container_patches)

    # Count how many times "Applying window size" was logged during container init
    apply_size_logs = [
        call
        for call in mock_log.info.call_args_list
        if len(call.args) > 0 and call.args[0] == "Applying window size"
    ]
    assert len(apply_size_logs) == 1
    assert apply_size_logs[0].kwargs["extra_info"] == {"width": 1600, "height": 900}

    # Verify initialize() does not reapply window size
    mock_log.info.reset_mock()
    from MyVideoExplorer.app.app_state_handler import AppStateHandler

    handler = AppStateHandler(container, window)
    handler.initialize()

    apply_size_after = [
        call
        for call in mock_log.info.call_args_list
        if len(call.args) > 0 and call.args[0] == "Applying window size"
    ]
    assert len(apply_size_after) == 0


def test_window_pos_changed_does_not_reapply_window_size(
    tmp_path, monkeypatch, container_patches
):
    QApplication.instance() or QApplication([])

    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    defaults_app_file = tmp_path / "defaults_app.json"
    settings_app_file = cfg_dir / "settings_app.json"

    default_data = {
        "launch_app_size": "app_size_1600x900",
        "launch_app_pos": "app_pos_center_center",
        "log_level": "info",
    }
    defaults_app_file.write_text(json.dumps(default_data), encoding="utf-8")
    settings_app_file.write_text(json.dumps(default_data), encoding="utf-8")

    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.DEFAULTS_APP_FILE", defaults_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.app.app_container.SETTINGS_APP_FILE", settings_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.DEFAULTS_APP_FILE", defaults_app_file
    )
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_state.SETTINGS_APP_FILE", settings_app_file
    )
    monkeypatch.setattr("MyVideoExplorer.settings.settings_state.CFG_DIR", cfg_dir)

    _, mock_log = container_patches
    _, container = _make_container(container_patches)

    mock_log.info.reset_mock()
    from MyVideoExplorer.app.app_signals import SignalPayload

    container.settings.settings_data_model.window_pos_changed.emit(
        SignalPayload(sender="test", data="app_pos_center_center")
    )

    apply_size_logs = [
        call
        for call in mock_log.info.call_args_list
        if len(call.args) > 0 and call.args[0] == "Applying window size"
    ]
    assert len(apply_size_logs) == 0
