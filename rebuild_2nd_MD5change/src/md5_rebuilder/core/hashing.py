from __future__ import annotations

from hashlib import md5
from pathlib import Path


def md5_file(path: Path, chunk_size: int = 1024 * 1024) -> str | None:
    digest = md5()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_size), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()

