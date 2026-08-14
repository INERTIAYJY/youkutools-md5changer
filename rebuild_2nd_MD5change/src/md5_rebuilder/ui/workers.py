from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from md5_rebuilder.core.models import RenderJob
from md5_rebuilder.services.encoder import VideoEncoder
from md5_rebuilder.services.probe import MediaProbe


class ProbeThread(QThread):
    finished_probe = Signal(str, object)

    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    def run(self) -> None:
        self.finished_probe.emit(str(self.path), MediaProbe().inspect(self.path))


class EncodeThread(QThread):
    progress = Signal(str, float)
    finished_encode = Signal(str, bool, str)

    def __init__(self, job: RenderJob):
        super().__init__()
        self.job = job
        self.encoder = VideoEncoder()

    def run(self) -> None:
        ok, message = self.encoder.encode(
            self.job,
            progress=lambda value: self.progress.emit(self.job.id, value),
        )
        self.finished_encode.emit(self.job.id, ok, message)

    def cancel(self) -> None:
        self.encoder.cancel()

