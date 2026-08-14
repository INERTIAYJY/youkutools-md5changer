from pathlib import Path

from md5_rebuilder.core.models import PRESETS, RateControl, RenderProfile, VideoOrientation
from md5_rebuilder.services.encoder import VideoEncoder, parse_progress
from md5_rebuilder.services.planner import JobPlanner
from md5_rebuilder.services.probe import MediaProbe


def test_parse_ffprobe_json():
    meta = MediaProbe(ffprobe=None).parse_ffprobe(
        {
            "format": {"duration": "9.5", "bit_rate": "3000000"},
            "streams": [
                {
                    "codec_type": "video",
                    "width": 720,
                    "height": 1280,
                    "codec_name": "h264",
                    "avg_frame_rate": "30/1",
                },
                {"codec_type": "audio", "codec_name": "aac", "bit_rate": "96000"},
            ],
        },
        Path("x.mp4"),
    )

    assert meta is not None
    assert meta.orientation == VideoOrientation.PORTRAIT
    assert meta.duration == 9.5
    assert meta.audio_codec == "aac"


def test_parse_ffmpeg_text():
    meta = MediaProbe(ffprobe=None).parse_ffmpeg_text(
        """
        Duration: 00:00:05.00, start: 0.000000, bitrate: 1234 kb/s
        Stream #0:0: Video: h264, yuv420p, 1920x1080, 25 fps
        Stream #0:1: Audio: aac, 44100 Hz, stereo, 128 kb/s
        """,
        Path("x.mp4"),
    )

    assert meta is not None
    assert meta.width == 1920
    assert meta.fps == 25
    assert meta.audio_bitrate == 128000


def test_progress_parser():
    assert parse_progress("out_time_ms=5000000", 10) == 50
    assert parse_progress("out_time=00:00:02.000000", 10) == 20


def test_command_and_planner(tmp_path: Path):
    src = tmp_path / "a.mp4"
    src.write_bytes(b"x")
    profile = RenderProfile(PRESETS[2], RateControl.CBR, bitrate_mbps=6.5)
    meta = MediaProbe(ffprobe=None).parse_ffmpeg_text(
        "Duration: 00:00:10.00, bitrate: 1000 kb/s\nStream #0:0: Video: h264, yuv420p, 1920x1080, 30 fps",
        src,
    )
    job = JobPlanner().plan([meta], profile)[0]
    command = VideoEncoder("ffmpeg").command_for(job)

    assert job.target.name == "a_new.mp4"
    assert "-progress" in command
    assert "scale=1920:1080" in command[command.index("-vf") + 1]
    assert "6.5M" in command
    assert "-c:a" in command


def test_command_can_disable_audio(tmp_path: Path):
    src = tmp_path / "silent.mp4"
    src.write_bytes(b"x")
    profile = RenderProfile(PRESETS[0], RateControl.CRF, include_audio=False)
    meta = MediaProbe(ffprobe=None).parse_ffmpeg_text(
        "Duration: 00:00:10.00, bitrate: 1000 kb/s\nStream #0:0: Video: h264, yuv420p, 1280x720, 30 fps",
        src,
    )
    job = JobPlanner().plan([meta], profile)[0]
    command = VideoEncoder("ffmpeg").command_for(job)

    assert "-an" in command
    assert "-c:a" not in command
