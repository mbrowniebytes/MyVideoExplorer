from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QWidget

from MyVideoExplorer.db.models.ffprobe_stats import FfprobeStats
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
    tab = SettingsMetaTab(state, MagicMock(), MagicMock())
    qtbot.addWidget(tab)
    return tab, stats_by_path


def test_meta_stats_show_selected_config_and_aggregate_scan_all(meta_tab):
    tab, _stats_by_path = meta_tab

    tab.scan_target_combo.setCurrentText("Movies")
    assert tab.scan_stats_label.text() == (
        "Probed files: 10 | Video streams: 10 | Audio streams: 20 | Subtitle streams: 3\n"
        "Last probed: 2026-11-08 08:30am"
    )

    tab.scan_target_combo.setCurrentText("Scan All")
    assert tab.scan_stats_label.text() == (
        "Probed files: 30 | Video streams: 30 | Audio streams: 60 | Subtitle streams: 9\n"
        "Last probed: 2026-11-09 09:45am"
    )


def test_meta_stats_refresh_after_scan_finishes(meta_tab):
    tab, stats_by_path = meta_tab
    tab.scan_target_combo.setCurrentText("Movies")
    stats_by_path["Movies"] = FfprobeStats(
        12, 12, 24, 4, datetime(2026, 11, 9, 10, 0, tzinfo=UTC)
    )
    tab._on_worker_stats_updated("Movies", stats_by_path["Movies"])

    assert "Probed files: 12 | Video streams: 12 | Audio streams: 24" in (
        tab.scan_stats_label.text()
    )
    assert "Last probed: 2026-11-09 10:00am" in tab.scan_stats_label.text()

    tab._current_worker = MagicMock()
    tab._scan_configs = [{"label": "Movies"}]
    tab._scan_index = 0

    tab._on_worker_finished()

    assert "Probed files: 12 | Video streams: 12 | Audio streams: 24" in (
        tab.scan_stats_label.text()
    )
    assert "Last probed: 2026-11-09 10:00am" in tab.scan_stats_label.text()


def test_meta_settings_footer_is_last_after_expanding_spacer(meta_tab):
    tab, _stats_by_path = meta_tab
    footer = tab.findChild(QWidget, "meta_settings_footer")

    assert footer is not None
    assert tab.content_layout.itemAt(tab.content_layout.count() - 1).widget() is footer
    assert tab.content_layout.itemAt(tab.content_layout.count() - 2).spacerItem()
