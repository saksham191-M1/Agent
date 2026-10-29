"""Small, deterministic sound-design cues, independent of paid narration.

The Studio renderer owns the timeline, so sound cues live here instead of in a
separate, fixed-length audio experiment.  A user-supplied file in
``assets/sfx`` always wins.  When one is not present, a short local cue is
generated with FFmpeg and cached; this keeps the normal SFX path offline and
does not consume narration credits.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .models import StudioError, timeline
from .editing import shot_plan


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SFX_ROOT = PROJECT_ROOT / "assets" / "sfx"
MUSIC_ROOT = PROJECT_ROOT / "assets" / "music"
MEDIA_SUFFIXES = (".wav", ".mp3", ".m4a", ".ogg", ".aac", ".flac")

# These are mix gains, not provider volume settings. The cue plan is deliberately
# sparse: one transition per edit, a restrained content hit, and one CTA resolve.
SFX_GAIN = {"whoosh": 0.16, "swipe": 0.14, "pop": 0.12, "ding": 0.18}

# A small cue language that maps naturally to the four Studio scene types.
# Generic scene names use the fallback rules below, so the same audio layer can
# serve story, comedy, POV, demo, and cinematic scene manifests too.
SFX_CUES = {
    "Hook": ("whoosh", 0.05),
    "Benefit": ("pop", 0.55),
    "Product": ("pop", 0.55),
    "Call to action": ("ding", 0.55),
}


def sfx_cues(scenes: list[dict]) -> list[tuple[str, float]]:
    """Return sparse cues that line up with the actual scene/shot edit points."""
    cues: list[tuple[str, float]] = []
    for index, scene in enumerate(timeline(scenes)):
        start = float(scene["start"])
        kind = str(scene.get("kind", "")).casefold()
        # Every scene starts with the same visual edit cue. The sound is not
        # pretending that a user clicked a button.
        cues.append(("whoosh", round(start + (0.03 if index else 0.0), 3)))
        if kind in {"benefit", "product", "demo", "action", "beat"}:
            cues.append(("pop", round(min(scene["end"] - 0.3, start + 0.28), 3)))
        if kind in {"cta", "call to action", "end card", "ending", "resolution"}:
            cues.append(("ding", round(min(scene["end"] - 0.35, start + 0.42), 3)))
    # Internal camera cuts use a short swipe only when there is a real visual
    # beat to support it. The renderer never emits fake UI-click sounds.
    cues.extend(("swipe", round(shot["start"] + 0.02, 3)) for shot in shot_plan(scenes) if shot["beat"])
    return sorted(cues, key=lambda cue: cue[1])


def _configured_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path if path.is_file() else None


def _local_media(root: Path, stem: str) -> Path | None:
    for suffix in MEDIA_SUFFIXES:
        path = root / f"{stem}{suffix}"
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def find_sfx(name: str) -> Path | None:
    """Find a user-supplied effect, if one exists."""
    configured = _configured_path(os.getenv(f"STUDIO_SFX_{name.upper()}"))
    return configured or _local_media(SFX_ROOT, name)


def find_music() -> Path | None:
    """Find an optional local music bed without scanning outside the project."""
    configured = _configured_path(os.getenv("STUDIO_MUSIC_PATH"))
    if configured:
        return configured
    for suffix in MEDIA_SUFFIXES:
        candidates = sorted(MUSIC_ROOT.glob(f"*{suffix}"))
        if candidates:
            return next((path for path in candidates if path.stat().st_size > 0), None)
    return None


def _generated_sfx(name: str, cache: Path) -> Path:
    """Create a clean fallback cue with FFmpeg's local signal generators."""
    specs = {
        "whoosh": (
            "anoisesrc=color=white:duration=0.55:sample_rate=48000:seed=42",
            "highpass=f=500,lowpass=f=6500,"
            "afade=t=in:st=0:d=0.03,afade=t=out:st=0.28:d=0.27,volume=0.8",
        ),
        "swipe": (
            "anoisesrc=color=pink:duration=0.24:sample_rate=48000:seed=42",
            "highpass=f=700,lowpass=f=5200,afade=t=in:st=0:d=0.015,"
            "afade=t=out:st=0.10:d=0.14,volume=0.9",
        ),
        "pop": (
            "sine=frequency=760:duration=0.16:sample_rate=48000",
            "afade=t=in:st=0:d=0.005,afade=t=out:st=0.06:d=0.10,volume=1.25",
        ),
        "ding": (
            "sine=frequency=1046.5:duration=0.45:sample_rate=48000",
            "afade=t=in:st=0:d=0.005,afade=t=out:st=0.15:d=0.30,volume=1.5",
        ),
    }
    if name not in specs:
        raise StudioError(f"Unsupported motion sound: {name}.")
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"studio-sfx-v4-{name}.wav"
    if target.is_file() and target.stat().st_size > 0:
        return target
    source, audio_filter = specs[name]
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", source,
             "-af", audio_filter, "-ar", "48000", "-ac", "2", str(target)],
            check=True, capture_output=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        raise StudioError(
            f"Motion SFX could not be prepared for '{name}'. Add assets/sfx/{name}.wav "
            "or turn Motion sound design off."
        ) from None
    return target


def get_sfx(name: str, cache: Path) -> Path:
    """Return a local effect, falling back to a cached deterministic cue."""
    return find_sfx(name) or _generated_sfx(name, cache)
