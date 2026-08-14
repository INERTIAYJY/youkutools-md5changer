from __future__ import annotations

import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any

from md5_rebuilder.core.models import PRESETS, ResolutionPreset, VideoMeta, VideoOrientation
from md5_rebuilder.utils.paths import ffmpeg_path, ffprobe_path


class MediaProbe:
    def __init__(self, ffmpeg: str | None = None, ffprobe: str | None = None):
        self.ffmpeg = ffmpeg or ffmpeg_path()
        self.ffprobe = ffprobe if ffprobe is not None else ffprobe_path()

    def inspect(self, path: Path) -> VideoMeta | None:
        if self.ffprobe:
            meta = self._inspect_json(path)
            if meta:
                return meta
        return self._inspect_text(path)

    def suggest_preset(self, meta: VideoMeta) -> ResolutionPreset:
        portrait = meta.orientation == VideoOrientation.PORTRAIT
        if portrait:
            label = "1080p 竖版" if meta.height >= 1080 else "720p 竖版"
        else:
            label = "1080p 横版" if meta.height >= 1080 else "720p 横版"
        return next(preset for preset in PRESETS if preset.label == label)

    def _inspect_json(self, path: Path) -> VideoMeta | None:
        command = [
            self.ffprobe,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ]
        try:
            result = subprocess.run(command, capture_output=True, timeout=30, check=False)
        except Exception:
            return None
        if result.returncode != 0:
            return None
        try:
            data = json.loads(result.stdout.decode("utf-8", errors="replace"))
        except Exception:
            return None
        return self.parse_ffprobe(data, path)

    def parse_ffprobe(self, data: dict[str, Any], path: Path) -> VideoMeta | None:
        streams = data.get("streams") or []
        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
        audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
        if not video:
            return None
        width = _int(video.get("width"))
        height = _int(video.get("height"))
        if width <= 0 or height <= 0:
            return None
        fmt = data.get("format") or {}
        return VideoMeta(
            path=path,
            width=width,
            height=height,
            duration=_float(video.get("duration")) or _float(fmt.get("duration")),
            video_codec=str(video.get("codec_name") or "unknown"),
            bitrate=_int(video.get("bit_rate")) or _int(fmt.get("bit_rate")),
            fps=_fps(video.get("avg_frame_rate") or video.get("r_frame_rate")),
            audio_codec=str(audio.get("codec_name")) if audio else None,
            audio_bitrate=_int(audio.get("bit_rate")) if audio else None,
        )

    def _inspect_text(self, path: Path) -> VideoMeta | None:
        try:
            result = subprocess.run(
                [self.ffmpeg, "-hide_banner", "-i", str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except Exception:
            return None
        return self.parse_ffmpeg_text((result.stderr or "") + "\n" + (result.stdout or ""), path)

    def parse_ffmpeg_text(self, text: str, path: Path) -> VideoMeta | None:
        video_line = next((line for line in text.splitlines() if " Video:" in line), "")
        audio_line = next((line for line in text.splitlines() if " Audio:" in line), "")
        size = re.search(r"(\d{2,5})x(\d{2,5})", video_line)
        if not size:
            return None
        duration = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", text)
        seconds = 0.0
        if duration:
            seconds = int(duration.group(1)) * 3600 + int(duration.group(2)) * 60 + float(duration.group(3))
        total_bitrate = re.search(r"bitrate:\s*(\d+)\s*kb/s", text)
        audio_bitrate = re.search(r"Audio:.*?(\d+)\s*kb/s", audio_line)
        codec = re.search(r"Video:\s*([^,\s]+)", video_line)
        audio = re.search(r"Audio:\s*([^,\s]+)", audio_line)
        fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", video_line)
        return VideoMeta(
            path=path,
            width=int(size.group(1)),
            height=int(size.group(2)),
            duration=seconds,
            video_codec=codec.group(1) if codec else "unknown",
            bitrate=int(total_bitrate.group(1)) * 1000 if total_bitrate else 0,
            fps=float(fps.group(1)) if fps else 0.0,
            audio_codec=audio.group(1) if audio else None,
            audio_bitrate=int(audio_bitrate.group(1)) * 1000 if audio_bitrate else None,
        )


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _fps(value: Any) -> float:
    try:
        return float(Fraction(str(value)))
    except Exception:
        return 0.0

