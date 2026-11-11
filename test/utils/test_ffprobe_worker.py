from __future__ import annotations

import logging
import subprocess
from unittest.mock import MagicMock

from PySide6.QtCore import Qt

from MyVideoExplorer.utils.ffprobe_util import FfprobeUtil
from MyVideoExplorer.utils.ffprobe_worker import FfprobeWorker


class _TrackingFfprobeWorker(FfprobeWorker):
    db_path: str
    run_returned: bool

    def _get_db_path(self) -> str:
        return self.db_path

    def run(self) -> None:
        super().run()
        self.run_returned = True


def test_worker_finished_signal_fires_after_run_returns(qtbot, tmp_path):
    worker = _TrackingFfprobeWorker(
        ffmpeg_folder=str(tmp_path),
        media_config={"label": "Empty"},
        scan_new_only=False,
        file_util=MagicMock(),
    )
    worker.db_path = str(tmp_path / "media.db")
    worker.run_returned = False
    completion_state: list[bool] = []
    worker.finished.connect(
        lambda: completion_state.append(worker.run_returned),
        Qt.ConnectionType.DirectConnection,
    )

    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.start()

    worker.wait()

    assert completion_state == [True]
    assert not worker.isRunning()


def test_probe_file_logs_ffprobe_error_details(tmp_path, monkeypatch, caplog):
    util = FfprobeUtil(str(tmp_path), str(tmp_path / "media.db"))
    completed = subprocess.CompletedProcess(
        args=[str(util.ffprobe_path)], returncode=1, stdout="", stderr="invalid input"
    )
    mock_run = MagicMock(return_value=completed)
    monkeypatch.setattr("MyVideoExplorer.utils.ffprobe_util.subprocess.run", mock_run)

    with caplog.at_level(logging.WARNING):
        assert util.probe_file("broken.mkv") is None

    assert "invalid input" in caplog.text
    assert mock_run.call_args.args[0][1:3] == ["-v", "error"]
