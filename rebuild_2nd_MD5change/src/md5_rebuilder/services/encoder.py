from __future__ import annotations

import subprocess
import threading
from collections.abc import Callable

from loguru import logger

from md5_rebuilder.core.models import RateControl, RenderJob
from md5_rebuilder.utils.paths import ffmpeg_path

ProgressFn = Callable[[float], None]


class EncodeCancelled(Exception):
    pass


class VideoEncoder:
    def __init__(self, ffmpeg: str | None = None):
        self.ffmpeg = ffmpeg or ffmpeg_path()
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()

    def command_for(self, job: RenderJob) -> list[str]:
        profile = job.profile
        preset = profile.preset
        cmd = [self.ffmpeg, "-hide_banner", "-y"]
        if profile.start_second is not None:
            cmd += ["-ss", f"{profile.start_second:.3f}"]
        cmd += ["-i", str(job.source)]
        if profile.clip_length is not None:
            cmd += ["-t", f"{profile.clip_length:.3f}"]
        elif profile.end_second is not None:
            cmd += ["-to", f"{profile.end_second:.3f}"]
        cmd += ["-progress", "pipe:1", "-nostats"]
        if profile.rate_control == RateControl.CBR:
            br = f"{profile.bitrate_mbps:.1f}M"
            cmd += ["-b:v", br, "-maxrate", br, "-bufsize", br]
        else:
            cmd += ["-crf", str(profile.crf), "-preset", "medium"]
        scale = (
            f"scale={preset.width}:{preset.height}:force_original_aspect_ratio=decrease,"
            f"pad={preset.width}:{preset.height}:(ow-iw)/2:(oh-ih)/2"
        )
        cmd += [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            scale,
        ]
        if profile.include_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000"]
        else:
            cmd += ["-an"]
        cmd += ["-movflags", "+faststart", str(job.target)]
        return cmd

    def encode(self, job: RenderJob, progress: ProgressFn | None = None) -> tuple[bool, str]:
        command = self.command_for(job)
        logger.info("Encoding {} -> {}", job.source, job.target)
        lines: list[str] = []
        try:
            if self._cancel_event.is_set():
                raise EncodeCancelled()
            with self._lock:
                self._process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if self._cancel_event.is_set():
                self._stop_process(self._process)
                raise EncodeCancelled()
            assert self._process.stdout is not None
            duration = self._job_duration(job)
            for raw in iter(self._process.stdout.readline, b""):
                line = raw.decode("utf-8", errors="replace").strip()
                if line:
                    lines.append(line)
                if self._cancel_event.is_set():
                    break
                percent = parse_progress(line, duration)
                if percent is not None and progress:
                    progress(percent)
                if self._process.poll() is not None:
                    break
            if self._cancel_event.is_set():
                self._stop_process(self._process)
                raise EncodeCancelled()
            code = self._process.wait()
            if code == 0:
                if progress:
                    progress(100.0)
                return True, "完成"
            return False, explain_failure(code, lines)
        except EncodeCancelled:
            return False, "用户已取消"
        except FileNotFoundError:
            return False, f"找不到 FFmpeg: {self.ffmpeg}"
        except Exception as exc:
            logger.exception("Encode failed")
            return False, f"编码异常: {exc}"
        finally:
            with self._lock:
                self._process = None

    def cancel(self) -> None:
        self._cancel_event.set()
        with self._lock:
            process = self._process
        self._stop_process(process)

    @staticmethod
    def _stop_process(process: subprocess.Popen[bytes] | None) -> None:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

    def _job_duration(self, job: RenderJob) -> float:
        if job.profile.clip_length is not None:
            return job.profile.clip_length
        if job.profile.start_second is not None:
            return max(1.0, job.source_duration - job.profile.start_second)
        if job.profile.end_second is not None:
            return max(1.0, job.profile.end_second)
        return max(1.0, job.source_duration)


def parse_progress(line: str, duration: float) -> float | None:
    if "=" not in line or duration <= 0:
        return None
    key, value = line.split("=", 1)
    seconds: float | None = None
    if key == "out_time_ms":
        try:
            seconds = int(value) / 1_000_000
        except ValueError:
            return None
    elif key == "out_time":
        seconds = _time_to_seconds(value)
    if seconds is None:
        return None
    return max(0.0, min(100.0, seconds / duration * 100))


def explain_failure(code: int | None, lines: list[str]) -> str:
    for line in reversed(lines):
        lowered = line.lower()
        if "error" in lowered or "invalid" in lowered or "failed" in lowered:
            return line[:500]
    if code == 0xC0000142:
        return "FFmpeg DLL 初始化失败，请安装或修复 Microsoft Visual C++ 运行库后重试"
    return f"FFmpeg 退出码: {code}"


def _time_to_seconds(value: str) -> float | None:
    try:
        hours, minutes, seconds = value.split(":")
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except ValueError:
        return None
