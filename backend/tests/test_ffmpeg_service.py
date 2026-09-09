import os
from pathlib import Path
from app.services.ffmpeg_service import ffmpeg_service
from app.core.config import settings


def test_ffmpeg_binary_detected():
    assert ffmpeg_service.ffmpeg_bin is not None
    assert os.path.exists(ffmpeg_service.ffmpeg_bin)


def test_generate_text_overlay_png(tmp_path):
    output_png = tmp_path / "test_overlay.png"
    text = "POV: you finally know what you're eating"
    ffmpeg_service._generate_text_overlay(text, output_png)

    assert output_png.exists()
    assert output_png.stat().st_size > 500  # Generated valid image bytes


def test_inspect_rendered_video_missing_file():
    import pytest
    from pathlib import Path
    with pytest.raises(FileNotFoundError):
        ffmpeg_service.inspect_rendered_video(Path("/tmp/non_existent_file_xyz_123.mp4"))
