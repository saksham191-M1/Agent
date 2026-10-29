"""Normalize user-supplied images before using them in local compositions."""
from pathlib import Path
import json
import math
import subprocess
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from .models import StudioError


def normalize_image(source: str, target: Path):
    path = Path(source)
    if not path.is_file() or path.stat().st_size > 20 * 1024 * 1024:
        raise StudioError("Upload a PNG, JPEG, or WebP image smaller than 20 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as original:
                if original.format not in ("PNG", "JPEG", "WEBP"):
                    raise StudioError("Logo and screenshot uploads must be PNG, JPEG, or WebP images.")
                if original.width * original.height > 24_000_000:
                    raise StudioError("Please resize the image to fewer than 24 million pixels before uploading.")
                image = ImageOps.exif_transpose(original).convert("RGBA")
                image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
                image.save(target, "PNG")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise StudioError("That image could not be decoded safely. Try another PNG, JPEG, or WebP.") from None


def normalize_video(source: str, target: Path, *, start_seconds: float = 0):
    """Copy genuine footage into a bounded, seekable H.264 product reference.

    Audio is controlled by the separate narration/SFX settings. No synthetic
    interface, cursor, action, or successful task is added to the recording.
    """
    path = Path(source)
    if (not path.is_file() or path.suffix.lower() not in (".mp4", ".mov", ".webm")
            or not 0 < path.stat().st_size <= 80 * 1024 * 1024):
        raise StudioError("Upload an MP4, MOV, or WebM product recording under 80 MB (2–120 seconds).")
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-show_format", "-show_streams",
             "-of", "json", str(path)], check=True, capture_output=True, timeout=30)
        info = json.loads(result.stdout)
        duration = float(info["format"]["duration"])
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        width, height = int(video["width"]), int(video["height"])
        if (not math.isfinite(duration) or not 2 <= duration <= 120 or not 0 < width * height <= 8_400_000
                or not math.isfinite(start_seconds) or not 0 <= start_seconds <= duration - 2
                or info["format"]["format_name"] not in ("mov,mp4,m4a,3gp,3g2,mj2", "matroska,webm")):
            raise ValueError
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, StopIteration, TypeError):
        raise StudioError("The product recording could not be verified. Use a 2–120 second MP4/MOV/WebM up to 4K; FFmpeg/ffprobe must be installed.") from None
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-protocol_whitelist", "file,pipe",
             "-ss", f"{start_seconds:.3f}", "-i", str(path),
             "-map", "0:v:0", "-an", "-vf", "scale=w='min(1920,iw)':h='min(1080,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,fps=30",
             "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
             "-map_metadata", "-1", "-movflags", "+faststart", str(target)],
            check=True, capture_output=True, timeout=240)
    except (OSError, subprocess.SubprocessError):
        target.unlink(missing_ok=True)
        raise StudioError("The product recording could not be prepared. Try an H.264 MP4 recording.") from None
    return {"duration": round(duration - start_seconds, 3)}
