from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# 必须在 sys.path 引导之后导入包（开发模式入口）
from md5_rebuilder.app import main  # noqa: E402

if __name__ == "__main__":
    main()
