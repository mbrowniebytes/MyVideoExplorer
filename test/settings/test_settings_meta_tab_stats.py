from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from MyVideoExplorer.db.models.ffprobe_stats import FfprobeStats
from MyVideoExplorer.lang.lang_en import LangEn
from MyVideoExplorer.settings.settings_meta_tab import SettingsMetaTab


@pytest.fixture
def meta_tab(qtbot, tmp_path, monkeypatch):
    configs = [
        {"label": "Movies", "path": str(tmp_path / "movies")},
        {"label": "TV", "path": str(tmp_path / "tv")},
    ]
    state = MagicMock()
    state.media_configs = configs
    state.ffmpeg_path = ""
    state.get_db_path.side_effect = lambda config: str(
        tmp_path / f"{config['label']}.db"
    )
    for config in configs:
        (tmp_path / f"{config['label']}.db").touch()

    stats_by_path = {
        "Movies": FfprobeStats(10, 10, 20, 3, datetime(2026, 11, 8, 8, 30, tzinfo=UTC)),
        "TV": FfprobeStats(20, 20, 40, 6, datetime(2026, 11, 9, 9, 45, tzinfo=UTC)),
    }
    monkeypatch.setattr(
        "MyVideoExplorer.settings.settings_meta_tab.FfprobeUtil",
        lambda _ffmpeg_path, _db_path: MagicMock(
            get_stats=lambda: stats_by_path.get(
                "Movies" if "Movies.db" in _db_path else "TV"
            )
        ),
    )
    tab = SettingsMetaTab(state, MagicMock(), MagicMock(), LangEn())
    qtbot.addWidget(tab)
    return tab, stats_by_path


def _get_stats_values(tab) -> list[str]:
    """Extract text from the value labels in scan_stats_layout."""
    values = []
    for i in range(tab.scan_stats_layout.count()):
        item = tab.scan_stats_layout.itemAt(i)
        if item is None:
            continue
        layout = item.layout()
        if layout is not None:
            for j in range(layout.count()):
                sub_item = layout.itemAt(j)
                if sub_item is not None:
                    widget = sub_item.widget()
                    if widget is not None and widget.objectName().startswith(
                        "meta_stats_val_"
                    ):
                        values.append(widget.text())
    return values


def _get_stats_tooltips(tab) -> list[str]:
    """Extract tooltips from the icon labels in scan_stats_layout."""
    tooltips = []
    for i in range(tab.scan_stats_layout.count()):
        item = tab.scan_stats_layout.itemAt(i)
        if item is None:
            continue
        layout = item.layout()
        if layout is not None:
            for j in range(layout.count()):
                sub_item = layout.itemAt(j)
                if sub_item is not None:
                    widget = sub_item.widget()
                    if widget is not None and widget.objectName().startswith(
                        "meta_stats_icon_"
                    ):
                        tooltips.append(widget.toolTip())
    return tooltips


def test_meta_stats_show_selected_config_and_aggregate_scan_all(meta_tab):
    tab, _stats_by_path = meta_tab

    tab.scan_target_combo.setCurrentText("Movies")
    values = _get_stats_values(tab)
    tooltips = _get_stats_tooltips(tab)
    assert values[0] == "10"  # Probed files
    assert tooltips[0] == "Probed files"
    assert values[1] == "10"  # Video streams
    assert values[2] == "20"  # Audio streams
    assert values[3] == "3"  # Subtitle streams
    assert "2026-11-08 08:30am" in tooltips[4]

    tab.scan_target_combo.setCurrentText("Scan All")
    values = _get_stats_values(tab)
    tooltips = _get_stats_tooltips(tab)
    assert values[0] == "30"  # Probed files (10 + 20)
    assert values[1] == "30"  # Video streams (10 + 20)
    assert values[2] == "60"  # Audio streams (20 + 40)
    assert values[3] == "9"  # Subtitle streams (3 + 6)
    assert "2026-11-09 09:45am" in tooltips[4]


def test_meta_stats_refresh_after_scan_finishes(meta_tab):
    tab, stats_by_path = meta_tab
    tab.scan_target_combo.setCurrentText("Movies")
    stats_by_path["Movies"] = FfprobeStats(
        12, 12, 24, 4, datetime(2026, 11, 9, 10, 0, tzinfo=UTC)
    )
    tab._on_worker_stats_updated("Movies", stats_by_path["Movies"])

    values = _get_stats_values(tab)
    tooltips = _get_stats_tooltips(tab)
    assert values[0] == "12"  # Probed files
    assert values[1] == "12"  # Video streams
    assert values[2] == "24"  # Audio streams
    assert "2026-11-09 10:00am" in tooltips[4]

    tab._current_worker = MagicMock()
    tab._scan_configs = [{"label": "Movies"}]
    tab._scan_index = 0

    tab._on_worker_finished()

    values = _get_stats_values(tab)
    tooltips = _get_stats_tooltips(tab)
    assert values[0] == "12"  # Probed files
    assert values[1] == "12"  # Video streams
    assert values[2] == "24"  # Audio streams
    assert "2026-11-09 10:00am" in tooltips[4]


def test_meta_settings_footer_is_last_after_expanding_spacer(meta_tab):
    tab, _stats_by_path = meta_tab
    footer = tab.findChild(QWidget, "meta_settings_footer")

    assert footer is not None
    assert tab.content_layout.itemAt(tab.content_layout.count() - 1).widget() is footer
    assert tab.content_layout.itemAt(tab.content_layout.count() - 2).spacerItem()
