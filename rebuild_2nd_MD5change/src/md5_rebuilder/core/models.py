from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4


class VideoOrientation(Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class RateControl(Enum):
    CBR = "CBR"
    CRF = "CRF"


class JobState(Enum):
    READY = "ready"
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def finished(self) -> bool:
        return self in {JobState.DONE, JobState.FAILED, JobState.CANCELLED}


@dataclass(frozen=True, slots=True)
class ResolutionPreset:
    label: str
    width: int
    height: int

    @property
    def orientation(self) -> VideoOrientation:
        return VideoOrientation.LANDSCAPE if self.width >= self.height else VideoOrientation.PORTRAIT


PRESETS: tuple[ResolutionPreset, ...] = (
    ResolutionPreset("720p 横版", 1280, 720),
    ResolutionPreset("720p 竖版", 720, 1280),
    ResolutionPreset("1080p 横版", 1920, 1080),
    ResolutionPreset("1080p 竖版", 1080, 1920),
)


@dataclass(frozen=True, slots=True)
class VideoMeta:
    path: Path
    width: int
    height: int
    duration: float
    video_codec: str
    bitrate: int = 0
    fps: float = 0.0
    audio_codec: str | None = None
    audio_bitrate: int | None = None

    @property
    def orientation(self) -> VideoOrientation:
        return VideoOrientation.LANDSCAPE if self.width >= self.height else VideoOrientation.PORTRAIT


@dataclass(frozen=True, slots=True)
class RenderProfile:
    preset: ResolutionPreset
    rate_control: RateControl
    bitrate_mbps: float = 8.0
    crf: int = 18
    start_second: float | None = None
    end_second: float | None = None
    output_dir: Path | None = None
    suffix: str = "new"
    include_audio: bool = True

    @property
    def clip_length(self) -> float | None:
        if self.start_second is not None and self.end_second is not None:
            return max(0.0, self.end_second - self.start_second)
        return None


@dataclass(slots=True)
class RenderJob:
    source: Path
    target: Path
    profile: RenderProfile
    source_duration: float = 0.0
    id: str = field(default_factory=lambda: uuid4().hex)
    state: JobState = JobState.READY
    progress: float = 0.0
    message: str = ""
    retries: int = 0
