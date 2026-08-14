from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from md5_rebuilder.ui.main_window import MainWindow
from md5_rebuilder.utils.logging import setup_logging
from md5_rebuilder.utils.paths import icon_path


def main() -> None:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("视频 MD5 重构工具")
    icon = icon_path()
    if icon:
        app.setWindowIcon(QIcon(str(icon)))
    window = MainWindow()
    if icon:
        window.setWindowIcon(QIcon(str(icon)))
    window.show()
    sys.exit(app.exec())
