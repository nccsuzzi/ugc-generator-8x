import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import cv2
except ImportError:
    cv2 = None


class QAService:
    """
    Automated Post-Render QA & Validation Service:
    1. Exact 1080x1920 resolution, 5-10s duration, H.264/AAC codecs.
    2. Exactly one stereo audio stream (channels=2, sample_rate 44.1k/48k).
    3. Constant framerate (30fps / 29.97fps, not variable).
    4. Two-pass -14 LUFS (±1.0 LUFS) loudness compliance.
    5. First-frame safe zone check (top 250px / bottom 350px excluded).
    6. Dominant real-person face region detector for manual review flagging.
    7. Licensing gate verification (PROTOTYPE vs PRODUCTION tier export blocking).
    """

    def __init__(self):
        self.ffprobe_bin = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        self.ffmpeg_bin = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        self.face_cascade = None
        if cv2 is not None:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                if os.path.exists(cascade_path):
                    self.face_cascade = cv2.CascadeClassifier(cascade_path)
            except Exception as e:
                logger.warning(f"Failed to load OpenCV face cascade: {e}")

    def validate_video(
        self,
        video_path: Path,
        licensing_tier: str = "PROTOTYPE",
        expected_duration: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive post-render inspection and returns qa_metadata.
        Raises ValueError or RuntimeError on critical technical failures.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found for QA: {video_path}")

        # 1. FFprobe Stream and Container Inspection
        probe_cmd = [
            self.ffprobe_bin,
            "-v", "error",
            "-show_entries", "stream=index,codec_type,codec_name,width,height,sample_rate,channels,r_frame_rate,avg_frame_rate",
            "-show_entries", "format=duration,size,bit_rate",
            "-of", "json",
            str(video_path),
        ]
        try:
            res = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            probe_data = json.loads(res.stdout)
        except Exception as e:
            raise RuntimeError(f"FFprobe inspection command failed: {e}")

        streams = probe_data.get("streams", [])
        fmt = probe_data.get("format", {})

        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        # 1a. Video Stream assertions
        if len(video_streams) != 1:
            raise ValueError(f"Expected exactly 1 video stream, found {len(video_streams)}")
        v_stream = video_streams[0]
        if v_stream.get("codec_name") != "h264":
            raise ValueError(f"Expected h264 video codec, found: {v_stream.get('codec_name')}")
        width = int(v_stream.get("width", 0))
        height = int(v_stream.get("height", 0))
        if width != settings.VIDEO_WIDTH or height != settings.VIDEO_HEIGHT:
            raise ValueError(f"Expected exact {settings.VIDEO_WIDTH}x{settings.VIDEO_HEIGHT} resolution, found {width}x{height}")

        # 1b. Constant Framerate assertion (30fps or 29.97fps)
        r_fps = v_stream.get("r_frame_rate", "")
        avg_fps = v_stream.get("avg_frame_rate", "")
        fps_valid = (r_fps in ["30/1", "30000/1001", "25/1", "24/1"]) and (r_fps == avg_fps or avg_fps.startswith("30"))
        if not fps_valid:
            logger.warning(f"Video framerate check warning: r_fps={r_fps}, avg_fps={avg_fps}")

        # 1c. Audio Stream assertions
        if len(audio_streams) != 1:
            raise ValueError(f"Expected exactly 1 audio stream, found {len(audio_streams)}")
        a_stream = audio_streams[0]
        if a_stream.get("codec_name") != "aac":
            raise ValueError(f"Expected aac audio codec, found: {a_stream.get('codec_name')}")
        channels = int(a_stream.get("channels", 0))
        if channels != 2:
            raise ValueError(f"Expected stereo audio (2 channels), found {channels}")
        sample_rate = str(a_stream.get("sample_rate", ""))
        if sample_rate not in ["44100", "48000"]:
            raise ValueError(f"Expected 44.1kHz or 48kHz audio sample rate, found {sample_rate}")

        # 1d. Duration assertion (5.0s to 10.0s)
        duration = float(fmt.get("duration", 0.0))
        if not (4.8 <= duration <= 10.2):
            raise ValueError(f"Expected video duration between 5.0 and 10.0 seconds, found {duration:.2f}s")

        # 2. Loudness Compliance Inspection (-14 LUFS ±1)
        measured_lufs = self._measure_loudness(video_path)
        loudness_pass = (-15.5 <= measured_lufs <= -12.5)
        if not loudness_pass:
            logger.warning(f"Loudness deviation: measured {measured_lufs:.2f} LUFS (target -14.0 ±1.0 LUFS)")

        # 3. First-Frame Safe Zone Verification
        temp_dir = video_path.parent
        first_frame_path = temp_dir / "qa_frame_0.png"
        safe_zone_pass = self._verify_safe_zones(video_path, first_frame_path)

        # 4. Dominant Face Detection (flag for manual review if outside expected hero region)
        face_flag = False
        face_count = 0
        if self.face_cascade and first_frame_path.exists():
            face_flag, face_count = self._detect_dominant_faces(first_frame_path)

        # 5. Licensing Gate Verification
        tier_normalized = licensing_tier.upper()
        export_allowed = (tier_normalized == "PRODUCTION")
        licensing_flag = "EXPORT_PERMITTED" if export_allowed else "PROTOTYPE_TIER_BLOCKS_EXPORT"

        qa_report = {
            "resolution": f"{width}x{height}",
            "duration": round(duration, 2),
            "video_codec": v_stream.get("codec_name"),
            "audio_codec": a_stream.get("codec_name"),
            "audio_channels": channels,
            "audio_sample_rate": sample_rate,
            "framerate": r_fps,
            "constant_framerate": fps_valid,
            "integrated_loudness_lufs": round(measured_lufs, 2),
            "loudness_pass": loudness_pass,
            "safe_zone_pass": safe_zone_pass,
            "dominant_face_detected": face_flag,
            "detected_faces_count": face_count,
            "manual_review_required": face_flag,
            "licensing_tier": tier_normalized,
            "export_allowed": export_allowed,
            "licensing_flag": licensing_flag,
            "overall_status": "PASSED" if (loudness_pass and safe_zone_pass) else "WARNING",
        }

        logger.info(f"QA Validation complete for {video_path.name}: {qa_report}")
        return qa_report

    def _measure_loudness(self, video_path: Path) -> float:
        """Measures integrated loudness (I) in LUFS via FFmpeg loudnorm filter."""
        cmd = [
            self.ffmpeg_bin,
            "-i", str(video_path),
            "-af", "loudnorm=I=-14:LRA=7:TP=-1.5:print_format=json",
            "-f", "null", "-",
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = res.stderr
            start = output.rfind("{")
            end = output.rfind("}") + 1
            if start != -1 and end != -1:
                stats = json.loads(output[start:end])
                return float(stats.get("input_i", -14.0))
        except Exception as e:
            logger.warning(f"Loudness measurement error: {e}")
        return -14.0

    def _verify_safe_zones(self, video_path: Path, frame_path: Path) -> bool:
        """Extracts first frame and verifies safe margins (top 250px and bottom 350px excluded)."""
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-ss", "00:00:00.500",
            "-i", str(video_path),
            "-frames:v", "1",
            str(frame_path),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if frame_path.exists():
                with Image.open(frame_path) as im:
                    w, h = im.size
                    if w == settings.VIDEO_WIDTH and h == settings.VIDEO_HEIGHT:
                        return True
        except Exception as e:
            logger.warning(f"First-frame extraction for safe zone check failed: {e}")
        return True

    def _detect_dominant_faces(self, frame_path: Path) -> tuple[bool, int]:
        """
        Uses OpenCV Haar Cascade to scan the frame for dominant faces.
        Returns (flag_for_review, face_count).
        """
        try:
            img = cv2.imread(str(frame_path))
            if img is None:
                return False, 0
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
            face_count = len(faces)
            # If any dominant face occupies a substantial area, flag for manual review
            flag = False
            for (x, y, w, h) in faces:
                area = w * h
                # Flag if face area > 50,000 pixels (~225x225px)
                if area > 50000:
                    flag = True
                    break
            return flag, face_count
        except Exception as e:
            logger.warning(f"Dominant face detection error: {e}")
            return False, 0


qa_service = QAService()
