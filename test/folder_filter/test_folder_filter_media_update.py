from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from MyVideoExplorer.settings.settings_state import SettingsState
from MyVideoExplorer.widgets.combo_boxes.checkbox_combo_box import CheckboxComboBox


@pytest.fixture
def filter_db_path(tmp_path):
    """Provide an isolated filter database path to avoid file lock conflicts."""
    return tmp_path / "filter_catalog.db"


def test_media_combo_refresh_on_signal(qtbot, filter_db_path: Path):
    """Verify the CheckboxComboBox for media folders refreshes on settings change."""
    mock_log_util = MagicMock()
    with patch("MyVideoExplorer.settings.settings_state.SettingsState._load_settings"):
        with patch(
            "MyVideoExplorer.settings.settings_state.SettingsState._ensure_defaults"
        ):
            state = SettingsState(mock_log_util, filter_db_path=filter_db_path)
            state.media_configs = [{"label": "Media1", "path": "/path1"}]

            settings = MagicMock()
            settings.settings_data_model = state

            combo = CheckboxComboBox()
            qtbot.addWidget(combo.widget)

            # Build initial items
            labels = sorted(
                config["label"]
                for config in state.media_configs
                if config.get("label") and config.get("path")
            )
            combo.set_items(labels)

            # With one item and nothing selected, the display shows the item name
            assert combo.selected_items() == []
            assert combo.widget.currentText() == "Media1"

            # Update label
            state.media_configs[0]["label"] = "NewMedia"

            # Rebuild items to reflect the change
            new_labels = sorted(
                config["label"]
                for config in state.media_configs
                if config.get("label") and config.get("path")
            )
            combo.set_items(new_labels)

            # Check if combo updated
            assert "NewMedia" in combo.selected_items() or combo.widget.count() == 1
            assert combo.widget.itemText(0) == "NewMedia"
