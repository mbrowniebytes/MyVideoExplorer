"""Tests for CompareWorker — background comparison task."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from MyVideoExplorer.compare.compare_worker import CompareWorker


class TestCompareWorker:
    """Test CompareWorker signal emission and execution."""

    @pytest.fixture(autouse=True)
    def _app(self):
        """Ensure a QApplication exists for QThread."""
        if not QApplication.instance():
            QApplication.instance()

    def test_worker_should_emit_finished_signal(
        self, local_test_db, compare_test_db, qtbot
    ):
        finished_count = []
        progress_messages = []

        worker = CompareWorker(
            local_db_path=Path(local_test_db),
            compare_db_path=Path(compare_test_db),
        )

        worker.finished.connect(lambda count: finished_count.append(count))
        worker.progress.connect(
            lambda current, total, msg: progress_messages.append(msg)
        )

        with qtbot.waitSignal(worker.finished, timeout=10000):
            worker.start()
            worker.wait()

        assert len(finished_count) == 1
        assert finished_count[0] > 0
        assert len(progress_messages) >= 2

    def test_worker_should_emit_progress_signals(
        self, local_test_db, compare_test_db, qtbot
    ):
        progress_messages = []

        worker = CompareWorker(
            local_db_path=Path(local_test_db),
            compare_db_path=Path(compare_test_db),
        )

        worker.progress.connect(
            lambda current, total, msg: progress_messages.append(msg)
        )

        with qtbot.waitSignal(worker.finished, timeout=10000):
            worker.start()
            worker.wait()

        assert "Loading local database" in progress_messages[0]
        assert "Comparison complete" in progress_messages[-1]

    def test_worker_should_emit_failed_on_bad_db(self, tmp_path, qtbot):
        failed_messages = []

        bad_path = tmp_path / "nonexistent.db"
        worker = CompareWorker(
            local_db_path=bad_path,
            compare_db_path=bad_path,
        )

        worker.failed.connect(lambda msg: failed_messages.append(msg))

        with qtbot.waitSignal(worker.failed, timeout=5000):
            worker.start()
            worker.wait()

        assert len(failed_messages) == 1

    def test_worker_should_complete_successfully(
        self, local_test_db, compare_test_db, qtbot
    ):
        finished_count = []
        failed_messages = []

        worker = CompareWorker(
            local_db_path=Path(local_test_db),
            compare_db_path=Path(compare_test_db),
        )

        worker.finished.connect(lambda count: finished_count.append(count))
        worker.failed.connect(lambda msg: failed_messages.append(msg))

        with qtbot.waitSignal(worker.finished, timeout=10000):
            worker.start()
            worker.wait()

        assert len(finished_count) == 1
        assert finished_count[0] > 0
        assert len(failed_messages) == 0
