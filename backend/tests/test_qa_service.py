import subprocess
from pathlib import Path
from PIL import Image
from app.services.qa_service import QAService


def test_qa_service_stream_validations(tmp_path):
    qa = QAService()
    dummy_mp4 = tmp_path / "test_valid.mp4"

    # Generate exact 1080x1920 30fps H.264 + AAC stereo 5-second video
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=5",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-ac", "2", "-ar", "44100",
        str(dummy_mp4),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    report = qa.validate_video(dummy_mp4, licensing_tier="PROTOTYPE")
    assert report["resolution"] == "1080x1920"
    assert report["video_codec"] == "h264"
    assert report["audio_codec"] == "aac"
    assert report["audio_channels"] == 2
    assert report["audio_sample_rate"] == "44100"
    assert report["licensing_tier"] == "PROTOTYPE"
    assert report["export_allowed"] is False
    assert report["licensing_flag"] == "PROTOTYPE_TIER_BLOCKS_EXPORT"
