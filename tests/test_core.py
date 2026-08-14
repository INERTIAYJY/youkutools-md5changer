from pathlib import Path

from md5_rebuilder.core.hashing import md5_file
from md5_rebuilder.core.models import PRESETS, RateControl, RenderProfile
from md5_rebuilder.core.naming import next_target_path, safe_suffix
from md5_rebuilder.utils.formatting import duration_text, size_text


def test_safe_suffix():
    assert safe_suffix("_a<b>") == "a_b_"
    assert safe_suffix("") == "new"


def test_next_target_path_original_dir(tmp_path: Path):
    source = tmp_path / "in.mp4"
    source.write_bytes(b"x")
    profile = RenderProfile(PRESETS[0], RateControl.CRF, suffix="new")

    assert next_target_path(source, profile) == tmp_path / "in_new.mp4"


def test_next_target_path_conflict(tmp_path: Path):
    source = tmp_path / "in.mp4"
    source.write_bytes(b"x")
    (tmp_path / "in_new.mp4").write_bytes(b"x")
    profile = RenderProfile(PRESETS[0], RateControl.CRF, suffix="new")

    assert next_target_path(source, profile) == tmp_path / "in_new_1.mp4"


def test_next_target_path_custom_dir_keeps_source_name(tmp_path: Path):
    source = tmp_path / "imported-video.mp4"
    source.write_bytes(b"x")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    profile = RenderProfile(PRESETS[2], RateControl.CRF, output_dir=output_dir, suffix="done")

    assert next_target_path(source, profile) == output_dir / "imported-video_done.mp4"


def test_hash_and_formatting(tmp_path: Path):
    path = tmp_path / "a.bin"
    path.write_bytes(b"abc")

    assert md5_file(path) == "900150983cd24fb0d6963f7d28e17f72"
    assert duration_text(65) == "01:05"
    assert size_text(1024) == "1.0 KB"
