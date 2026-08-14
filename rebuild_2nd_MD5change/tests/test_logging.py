import sys

from md5_rebuilder.utils.logging import setup_logging


def test_setup_logging_without_stderr(monkeypatch):
    monkeypatch.setattr(sys, "stderr", None)

    setup_logging()
