from unittest.mock import MagicMock

import pytest

from MyVideoExplorer.settings.settings_media_folder_browser_section import (
    SettingsMediaFolderBrowserSection,
)
from MyVideoExplorer.settings.settings_media_tab import SettingsMediaTab


class TestSettingsMediaScanAll:
    @pytest.fixture
    def media_tab(self, qtbot, tmp_path):
        folder1 = tmp_path / "movies"
        folder1.mkdir()
        folder2 = tmp_path / "tv"
        folder2.mkdir()

        mock_state = MagicMock()
        mock_state.media_configs = [
            {"label": "Movies", "path": str(folder1)},
            {"label": "TV", "path": str(folder2)},
        ]
        mock_state.db_enabled.return_value = True
        mock_state.get_db_path.return_value = str(tmp_path / "media.db")

        mock_log = MagicMock()
        mock_file_util = MagicMock()

        tab = SettingsMediaTab(mock_state, mock_log, mock_file_util)
        qtbot.addWidget(tab)
        return tab

    def test_scan_all_button_exists_and_state(self, media_tab):
        assert hasattr(media_tab, "scan_all_btn")
        assert media_tab.scan_all_btn.text() == "Scan All"
        assert media_tab.scan_all_btn.isEnabled()
        sections = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )
        assert sections
        assert all(not section.scan_btn.icon().isNull() for section in sections)

    def test_media_scan_timeout_uses_app_setting(self, media_tab):
        media_tab.state.scan_media_timeout_seconds = 60
        section = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )[0]

        assert section.scan_timeout_seconds() == 60

    def test_scan_all_sequential_execution(self, media_tab, monkeypatch):
        sections = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )
        assert len(sections) == 2
        sec1, sec2 = sections
        started: list[SettingsMediaFolderBrowserSection] = []
        visible_progress_bars = []
        monkeypatch.setattr(
            media_tab.folder_scroll_area,
            "ensureWidgetVisible",
            lambda widget, xmargin=50, ymargin=50: visible_progress_bars.append(
                (widget, xmargin, ymargin)
            ),
        )
        monkeypatch.setattr(sec1, "start_scan", lambda: started.append(sec1) or True)
        monkeypatch.setattr(sec2, "start_scan", lambda: started.append(sec2) or True)

        # Click Scan All
        media_tab._on_scan_all_clicked()

        # Should be disabled and scanning 1 of 2
        assert not media_tab.scan_all_btn.isEnabled()
        assert "Scanning 1 of 2" in media_tab.scan_all_btn.text()
        assert started == [sec1]
        assert visible_progress_bars == [(sec1.progress_bar, 12, 24)]

        # Section 1 finishes
        sec1.scan_finished.emit()

        # Should now be scanning 2 of 2
        assert not media_tab.scan_all_btn.isEnabled()
        assert "Scanning 2 of 2" in media_tab.scan_all_btn.text()
        assert started == [sec1, sec2]
        assert visible_progress_bars[-1] == (sec2.progress_bar, 12, 24)

        # Section 2 finishes
        sec2.scan_finished.emit()

        # Should be re-enabled and text reset
        assert media_tab.scan_all_btn.isEnabled()
        assert media_tab.scan_all_btn.text() == "Scan All"

    def test_scan_all_advances_after_start_failure(self, media_tab, monkeypatch):
        sections = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )
        sec1, sec2 = sections
        started: list[SettingsMediaFolderBrowserSection] = []
        monkeypatch.setattr(sec1, "start_scan", lambda: started.append(sec1) or False)
        monkeypatch.setattr(sec2, "start_scan", lambda: started.append(sec2) or True)

        media_tab._on_scan_all_clicked()

        assert started == [sec1, sec2]
        assert "Scanning 2 of 2" in media_tab.scan_all_btn.text()
        assert not media_tab.scan_all_btn.isEnabled()

        sec2.scan_finished.emit()

        assert media_tab.scan_all_btn.isEnabled()
        assert media_tab.scan_all_btn.text() == "Scan All"

    def test_scan_all_button_shows_stalled_status(self, media_tab, monkeypatch):
        section = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )[0]
        monkeypatch.setattr(section, "start_scan", lambda: True)

        media_tab._on_scan_all_clicked()
        section.scan_stalled.emit()

        assert "Stopping stalled scan 1 of 2" in media_tab.scan_all_btn.text()

    def test_scan_stall_timeout_requests_cooperative_stop(self, media_tab):
        section = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )[0]
        worker = MagicMock()
        worker.isRunning.return_value = True
        section.worker = worker

        section._on_scan_stalled()

        worker.requestInterruption.assert_called_once_with()
        assert section.scan_btn.text() == "Stopping..."
        assert section.progress_bar.isTextVisible()
        assert "120 seconds" in section.progress_bar.format()

    def test_start_scan_reports_preflight_failure(self, media_tab, monkeypatch):
        section = media_tab.folder_nav_content.findChildren(
            SettingsMediaFolderBrowserSection
        )[0]

        def fail_rename(_media_config):
            raise ValueError("Database name conflict")

        monkeypatch.setattr(section, "_rename_db_file_if_needed", fail_rename)
        monkeypatch.setattr(
            "MyVideoExplorer.settings.settings_media_folder_browser_section.QMessageBox.critical",
            lambda *_args: None,
        )

        assert section.start_scan() is False
