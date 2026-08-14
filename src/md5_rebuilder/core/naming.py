from __future__ import annotations

import re
from pathlib import Path

from md5_rebuilder.core.models import RenderProfile

BAD_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_suffix(value: str | None) -> str:
    suffix = (value or "new").strip().lstrip("_")
    suffix = BAD_CHARS.sub("_", suffix)
    return suffix or "new"


def next_target_path(source: Path, profile: RenderProfile) -> Path:
    target_dir = profile.output_dir or source.parent
    suffix = safe_suffix(profile.suffix)
    base = f"{source.stem}_{suffix}"
    candidate = target_dir / f"{base}{source.suffix}"
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        candidate = target_dir / f"{base}_{index}{source.suffix}"
        if not candidate.exists():
            return candidate
        index += 1
