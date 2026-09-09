import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from app.core.config import settings
from app.schemas.creative import CreativePlan
from app.services.qa_service import qa_service
from app.utils.file_utils import ensure_dir, safe_cleanup_dir

logger = logging.getLogger(__name__)


class FFmpegService:
    """
    Deterministic 4-layer UGC video assembly service:
    Layer 1: 1080x1920 vertical background video with consistent cinematic color-grade LUT
    Layer 2: Looping reaction GIF overlay (HERO visual, 65-75% width, soft edge mask & shadow, top-third placement)
    Layer 3: Free-floating bold hook text overlay with stroke + drop shadow and karaoke-style highlighting
    Layer 4: Epidemic Sound soundtrack with two-pass -14 LUFS loudness normalization and stereo fades
    """

    def __init__(self):
        self.ffmpeg_bin = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        self.ffprobe_bin = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"

    def render_video(
        self,
        video_id: str,
        plan: CreativePlan,
        background_path: Path,
        gif_path: Path,
        audio_path: Path,
        licensing_tier: str = "PROTOTYPE",
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Renders the final MP4 video, executes two-pass audio normalization,
        applies soft feathered edge mask on reaction GIF, generates free-floating typography,
        runs comprehensive QA validation, and returns (output_mp4_path, qa_report).
        """
        temp_dir = ensure_dir(settings.TEMP_DIR / video_id)
        output_mp4 = temp_dir / "output.mp4"

        duration = max(5, min(10, plan.duration or settings.VIDEO_DURATION))
        width = settings.VIDEO_WIDTH
        height = settings.VIDEO_HEIGHT

        # 1. Measure reaction GIF natural aspect ratio to compute target dimensions
        with Image.open(gif_path) as im:
            orig_w, orig_h = im.size

        if plan.gif_position == "webcam":
            # Corner webcam bubble
            target_gif_width = 380
            target_gif_height = int(target_gif_width * (orig_h / orig_w))
            target_gif_height = min(420, max(300, target_gif_height))
            gif_x = width - target_gif_width - 60
            gif_y = settings.SAFE_ZONE_TOP + 30
        else:
            # Hero top-third placement (65% to 75% canvas width)
            gif_scale = max(0.65, min(0.75, plan.gif_scale or 0.70))
            target_gif_width = int(width * gif_scale)
            target_gif_height = int(target_gif_width * (orig_h / orig_w))
            # Clamp height to stay comfortably inside safe margins (y=250 to 1570)
            target_gif_height = min(780, max(460, target_gif_height))
            gif_x = (width - target_gif_width) // 2
            gif_y = 460

        # 2. Generate soft feathered mask & drop shadow PNGs for GIF
        mask_png = temp_dir / "gif_feather_mask.png"
        shadow_png = temp_dir / "gif_drop_shadow.png"
        self._generate_gif_mask_and_shadow(
            width=target_gif_width,
            height=target_gif_height,
            mask_path=mask_png,
            shadow_path=shadow_png,
        )
        shadow_x = gif_x - 20
        shadow_y = gif_y - 15

        # 3. Generate free-floating bold text overlay frames (karaoke word-by-word highlighting)
        text_frames = self._generate_karaoke_text_overlays(
            text=plan.text_overlay,
            duration=duration,
            output_dir=temp_dir,
        )

        # 4. Pass 1: Loudnorm audio measurement
        loudnorm_params = self._measure_loudnorm(audio_path)

        # 5. Audio Fade parameters
        fade_out_start = max(1.0, duration - 0.5)

        # 6. Build Filter Complex
        filter_inputs = [
            f"-stream_loop -1 -an -i {background_path}",
            f"-ignore_loop 0 -i {gif_path}",
            f"-stream_loop -1 -i {audio_path}",
            f"-i {mask_png}",
            f"-i {shadow_png}",
        ]
        next_input_idx = 5
        text_input_indices = []
        for tf in text_frames:
            filter_inputs.append(f"-i {tf['path']}")
            text_input_indices.append((next_input_idx, tf["start"], tf["end"]))
            next_input_idx += 1

        # Background color grade & crop
        filter_parts = [
            f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            f"eq=saturation=1.08:contrast=1.04:brightness=-0.02,"
            f"colorbalance=rs=0.03:gs=-0.01:bs=-0.02,"
            f"fps={settings.VIDEO_FPS},"
            f"trim=0:{duration},"
            f"setpts=PTS-STARTPTS[bg];",
            # Scale reaction GIF and apply soft feathered alpha mask
            f"[1:v]scale={target_gif_width}:{target_gif_height}:flags=lanczos,format=rgba[scaled_gif];",
            f"[3:v]scale={target_gif_width}:{target_gif_height}[scaled_mask];",
            f"[scaled_gif][scaled_mask]alphamerge[feathered_gif];",
            # Overlay shadow, then feathered GIF onto background
            f"[bg][4:v]overlay={shadow_x}:{shadow_y}[bg_shadow];",
            f"[bg_shadow][feathered_gif]overlay={gif_x}:{gif_y}:shortest=0[bg_with_gif];",
        ]

        # Chain text overlay frames with time windows
        current_v = "bg_with_gif"
        for idx, (in_idx, t_start, t_end) in enumerate(text_input_indices):
            out_v = f"v_text_{idx}" if idx < len(text_input_indices) - 1 else "final_video"
            filter_parts.append(
                f"[{current_v}][{in_idx}:v]overlay=0:0:enable='between(t,{t_start:.2f},{t_end:.2f})'[{out_v}];"
            )
            current_v = out_v

        # Pass 2 Audio loudnorm filter + in/out fades
        filter_parts.append(
            f"[2:a:0]aformat=channel_layouts=stereo:sample_rates=44100,"
            f"loudnorm=I=-14:LRA=7:TP=-1.5:"
            f"measured_I={loudnorm_params['input_i']}:"
            f"measured_LRA={loudnorm_params['input_lra']}:"
            f"measured_TP={loudnorm_params['input_tp']}:"
            f"measured_thresh={loudnorm_params['input_thresh']}:"
            f"offset={loudnorm_params['target_offset']}:linear=true,"
            f"afade=t=in:ss=0:d=0.3,"
            f"afade=t=out:st={fade_out_start:.2f}:d=0.5,"
            f"atrim=0:{duration},asetpts=PTS-STARTPTS[final_audio]"
        )

        filter_complex = "".join(filter_parts)

        # Assemble CLI Command
        cmd = [self.ffmpeg_bin, "-y"]
        # Split filter inputs into list args
        for inp_str in filter_inputs:
            cmd.extend(inp_str.split())

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[final_video]",
            "-map", "[final_audio]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "21",
            "-pix_fmt", "yuv420p",
            "-r", str(settings.VIDEO_FPS),
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-ac", "2",
            "-t", str(duration),
            "-movflags", "+faststart",
            str(output_mp4),
        ])

        logger.info(f"Rendering UGC video {video_id} with FFmpeg (duration={duration}s)...")
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg assembly failed: {e.stderr}")
            safe_cleanup_dir(temp_dir)
            raise RuntimeError(f"FFmpeg render failed: {e.stderr[-300:]}")

        if not output_mp4.exists() or output_mp4.stat().st_size == 0:
            safe_cleanup_dir(temp_dir)
            raise RuntimeError("FFmpeg completed but output MP4 is empty or missing.")

        # 7. Post-Render Automated QA & Validation Check
        qa_report = qa_service.validate_video(
            video_path=output_mp4,
            licensing_tier=licensing_tier,
            expected_duration=duration,
        )

        return output_mp4, qa_report

    def _measure_loudnorm(self, audio_path: Path) -> Dict[str, str]:
        """Pass 1 loudnorm measurement to extract exact calibration parameters."""
        cmd = [
            self.ffmpeg_bin,
            "-i", str(audio_path),
            "-af", "loudnorm=I=-14:LRA=7:TP=-1.5:print_format=json",
            "-f", "null", "-",
        ]
        defaults = {
            "input_i": "-20.0",
            "input_lra": "7.0",
            "input_tp": "-2.0",
            "input_thresh": "-30.0",
            "target_offset": "0.0",
        }
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = res.stderr
            start = output.rfind("{")
            end = output.rfind("}") + 1
            if start != -1 and end != -1:
                stats = json.loads(output[start:end])
                return {
                    "input_i": stats.get("input_i", "-20.0"),
                    "input_lra": stats.get("input_lra", "7.0"),
                    "input_tp": stats.get("input_tp", "-2.0"),
                    "input_thresh": stats.get("input_thresh", "-30.0"),
                    "target_offset": stats.get("target_offset", "0.0"),
                }
        except Exception as e:
            logger.warning(f"Pass 1 loudnorm measurement failed: {e}, using defaults")
        return defaults

    def _generate_gif_mask_and_shadow(
        self,
        width: int,
        height: int,
        mask_path: Path,
        shadow_path: Path,
    ) -> None:
        """Generates a feathered rounded alpha mask and soft drop shadow for the GIF."""
        # 1. Feathered alpha mask
        mask = Image.new("L", (width, height), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([6, 6, width - 6, height - 6], radius=28, fill=255)
        feathered_mask = mask.filter(ImageFilter.GaussianBlur(radius=5))
        feathered_mask.save(str(mask_path))

        # 2. Soft drop shadow (extra padding for gaussian blur spread)
        pad = 40
        shadow = Image.new("RGBA", (width + pad, height + pad), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.rounded_rectangle(
            [20, 20, width + 20, height + 20],
            radius=28,
            fill=(0, 0, 0, 160),
        )
        feathered_shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
        feathered_shadow.save(str(shadow_path))

    def _generate_karaoke_text_overlays(
        self,
        text: str,
        duration: float,
        output_dir: Path,
    ) -> List[Dict[str, Any]]:
        """
        Renders free-floating bold text overlay frames with stroke + drop shadow.
        Generates word-by-word highlighted frames (karaoke-style in TikTok yellow #FFE600).
        """
        font = self._load_bold_font(size=56)
        words = text.strip().split()
        if not words:
            words = ["POV:", "Check", "this", "out"]

        # Word-wrap into maximum 2 punchy lines
        lines_words = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            if len(test_line) > 24:
                if len(current_line) > 1:
                    current_line.pop()
                    lines_words.append(current_line)
                    current_line = [word]
                else:
                    lines_words.append(current_line)
                    current_line = []
        if current_line:
            lines_words.append(current_line)

        # Measure text line widths and heights
        dummy_img = Image.new("RGBA", (settings.VIDEO_WIDTH, settings.VIDEO_HEIGHT))
        draw = ImageDraw.Draw(dummy_img)

        line_height = 76
        start_y = settings.SAFE_ZONE_TOP + 30  # y = 280 (comfortably inside safe margin)
        center_x = settings.VIDEO_WIDTH // 2

        # Flatten word coordinates
        word_positions = []
        word_counter = 0
        for line_idx, line in enumerate(lines_words):
            full_line_str = " ".join(line)
            bbox = draw.textbbox((0, 0), full_line_str, font=font)
            line_w = bbox[2] - bbox[0]
            cur_x = center_x - (line_w // 2)
            cur_y = start_y + (line_idx * line_height)

            for w in line:
                word_bbox = draw.textbbox((0, 0), w, font=font)
                w_width = word_bbox[2] - word_bbox[0]
                space_bbox = draw.textbbox((0, 0), " ", font=font)
                space_w = space_bbox[2] - space_bbox[0]

                word_positions.append({
                    "word_idx": word_counter,
                    "word": w,
                    "x": cur_x,
                    "y": cur_y,
                })
                cur_x += w_width + space_w
                word_counter += 1

        total_words = len(word_positions)
        word_duration = duration / max(1, total_words)

        frames = []
        for highlight_idx in range(total_words):
            canvas = Image.new("RGBA", (settings.VIDEO_WIDTH, settings.VIDEO_HEIGHT), (0, 0, 0, 0))
            fdraw = ImageDraw.Draw(canvas)

            for wp in word_positions:
                is_active = (wp["word_idx"] == highlight_idx)
                text_color = (255, 230, 0, 255) if is_active else (255, 255, 255, 255)
                # Drop shadow
                fdraw.text(
                    (wp["x"] + 5, wp["y"] + 5),
                    wp["word"],
                    font=font,
                    fill=(0, 0, 0, 210),
                    stroke_width=6,
                    stroke_fill=(0, 0, 0, 210),
                )
                # Free-floating bold text with thick dark outline
                fdraw.text(
                    (wp["x"], wp["y"]),
                    wp["word"],
                    font=font,
                    fill=text_color,
                    stroke_width=6,
                    stroke_fill=(0, 0, 0, 255),
                )

            frame_path = output_dir / f"text_frame_{highlight_idx}.png"
            canvas.save(str(frame_path), "PNG")

            t_start = highlight_idx * word_duration
            t_end = duration if highlight_idx == total_words - 1 else (highlight_idx + 1) * word_duration
            frames.append({
                "path": frame_path,
                "start": t_start,
                "end": t_end,
            })

        return frames

    def _load_bold_font(self, size: int = 56) -> ImageFont.FreeTypeFont:
        font_candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        for candidate in font_candidates:
            if os.path.exists(candidate):
                try:
                    return ImageFont.truetype(candidate, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _generate_text_overlay(self, text: str, output_path: Path) -> None:
        """Renders single free-floating bold stroke+shadow text overlay."""
        frames = self._generate_karaoke_text_overlays(text, duration=7.0, output_dir=output_path.parent)
        if frames and frames[0]["path"].exists():
            shutil.copy(frames[0]["path"], output_path)

    def inspect_rendered_video(self, video_path: Path) -> Dict[str, Any]:
        """Validates rendered video via QAService."""
        return qa_service.validate_video(video_path)


ffmpeg_service = FFmpegService()
