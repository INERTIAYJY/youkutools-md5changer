from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from md5_rebuilder.utils.paths import data_home


class SettingsStore:
    defaults = {
        "preset": "1080p 横版",
        "rate_control": "CRF",
        "bitrate_mbps": 8.0,
        "crf": 18,
        "suffix": "new",
        "include_audio": True,
        "theme": "auto",
    }

    def __init__(self, path: Path | None = None):
        self.path = path or data_home() / "settings.json"
        self.data = self._read()

    def _read(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        return {**self.defaults, **raw} if isinstance(raw, dict) else self.defaults.copy()

    def save(self, updates: dict[str, Any]) -> None:
        self.data.update({key: value for key, value in updates.items() if key != "output_dir"})
        self.data.pop("output_dir", None)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
