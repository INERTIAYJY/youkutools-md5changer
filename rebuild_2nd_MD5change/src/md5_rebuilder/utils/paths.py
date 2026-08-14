from __future__ import annotations

import os
import sys
from pathlib import Path


def app_root() -> Path:
    return Path(__file__).resolve().parents[3]


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return Path(sys.executable).resolve().parent
    return app_root()


def data_home() -> Path:
    path = Path.home() / ".md5_rebuilder"
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        fallback = app_root() / ".runtime"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def find_tool(name: str) -> str | None:
    exe_name = f"{name}.exe" if os.name == "nt" else name
    env_bin = os.environ.get("FFMPEG_BIN")
    candidates: list[Path] = []
    if env_bin:
        env_path = Path(env_bin)
        candidates.append(env_path / exe_name if env_path.is_dir() else env_path)
    candidates.extend(
        [
            runtime_root() / "ffmpeg_bin" / exe_name,
            Path(sys.executable).resolve().parent / "ffmpeg_bin" / exe_name,
            app_root() / "ffmpeg_bin" / exe_name,
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def ffmpeg_path() -> str:
    return find_tool("ffmpeg") or "ffmpeg"


def ffprobe_path() -> str | None:
    return find_tool("ffprobe")


def resources_dir() -> Path | None:
    package_dir = Path(__file__).resolve().parent.parent / "resources"
    for candidate in [package_dir, runtime_root() / "resources", app_root() / "resources"]:
        if candidate.is_dir():
            return candidate
    return None


def icon_path() -> Path | None:
    base = resources_dir()
    if base:
        icon = base / "app.ico"
        if icon.exists():
            return icon
    return None

