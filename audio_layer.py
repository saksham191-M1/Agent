"""
audio_layer.py
Per-scene ElevenLabs voice lines + SFX -> ONE timed mix track (wav), muxed by programmatic_pipeline.encode().

Env vars: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
Requires: requests, ffmpeg + ffprobe on PATH.
"""
import json
import hashlib
import os
import subprocess
from pathlib import Path

import requests

API = "https://api.elevenlabs.io/v1"
TTS_MODEL = "eleven_multilingual_v2"
DURATION = 15
PROJECT_ROOT = Path(__file__).resolve().parent
SFX_DIR = PROJECT_ROOT / "assets" / "sfx"
CACHE = PROJECT_ROOT / "output" / "audio_cache"
VOICES_FILE = PROJECT_ROOT / "tools" / "video_pipeline" / "voices.json"
WORDS_PER_SEC = 2.4      # comfortable ad pacing
MAX_SPEEDUP = 1.15       # never speed a voice line up more than this
VO_GAIN, SFX_GAIN = 1.0, 0.35

# (field, start_s, latest_end_s) per voice line; (sfx_name, time_s) per sound effect.
_BASE = {
    "vo": [("VO_1", 0.3, 2.0), ("VO_2", 2.2, 5.0), ("VO_3", 5.3, 10.0), ("VO_4", 10.3, 14.7)],
    "sfx": [("whoosh", 0.0), ("pop", 2.2), ("whoosh", 5.0), ("pop", 5.6),
            ("pop", 6.4), ("whoosh", 10.0), ("ding", 12.8)],
}
CUES = {"iphone_showcase_master": _BASE, "problem_solution_master": _BASE}

SFX_PROMPTS = {
    "whoosh": "short clean cinematic whoosh transition, under one second",
    "pop": "soft UI pop notification, very short, clean",
    "ding": "bright clean success chime, short",
    "click": "crisp mechanical mouse click",
    "tick": "minimal watch tick sound",
}


def load_voices() -> dict:
    if VOICES_FILE.exists():
        try:
            with open(VOICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "fast_confident": {"voice_id": "21m00Tcm4TlvDq8ikWAM", "stability": 0.45, "similarity_boost": 0.85, "speed": 1.15},
        "confident_engineer": {"voice_id": "VR6AewLTigWG4xSOukaG", "stability": 0.60, "similarity_boost": 0.80, "speed": 1.05},
        "calm_precise": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "stability": 0.70, "similarity_boost": 0.85, "speed": 0.98},
        "warm_conversational": {"voice_id": "AZnzlk1XvdvUeBnXmlld", "stability": 0.50, "similarity_boost": 0.75, "speed": 1.02},
        "energetic": {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "stability": 0.40, "similarity_boost": 0.85, "speed": 1.18}
    }


def resolve_voice(voice_style: str = "fast_confident") -> dict:
    voices = load_voices()
    return voices.get(voice_style) or voices.get("fast_confident")


class VoiceTooLong(Exception):
    pass


def _headers():
    return {"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", ""), "Content-Type": "application/json"}


# ------------------------------------------------ helpers for the JSON brain
def vo_fields(template: str) -> list[str]:
    return [f for f, _, _ in CUES[template]["vo"]]


def vo_char_limits(template: str) -> dict[str, int]:
    return {f: int((end - start) * WORDS_PER_SEC) * 7 for f, start, end in CUES[template]["vo"]}


def prompt_addendum(template: str) -> str:
    lines = [f"- {f}: at most {int((e - s) * WORDS_PER_SEC)} words" for f, s, e in CUES[template]["vo"]]
    return (
        "\nThe VO_ fields are spoken voiceover lines, one per scene, in order: hook, problem or feature, "
        "payoff, call to action. They are full conversational sentences (this overrides the headline "
        "length rule), must match the on-screen text of their scene, and must not repeat each other.\n"
        + "\n".join(lines) + "\n"
    )


# ------------------------------------------------------------- audio sources
def tts(text: str, voice_style: str = "fast_confident", voice_id_override: str = None) -> Path:
    voice_cfg = resolve_voice(voice_style)
    voice = voice_id_override or os.environ.get("ELEVENLABS_VOICE_ID") or voice_cfg.get("voice_id", "21m00Tcm4TlvDq8ikWAM")
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("[AudioLayer] Warning: ELEVENLABS_API_KEY missing. Skipping TTS generation.")
        return None
        
    key = hashlib.sha1(f"{voice}|{TTS_MODEL}|{voice_style}|{text}".encode()).hexdigest()[:16]
    path = CACHE / f"{key}.mp3"
    if path.exists():
        return path
    CACHE.mkdir(parents=True, exist_ok=True)
    r = requests.post(
        f"{API}/text-to-speech/{voice}", headers=_headers(), timeout=60,
        json={"text": text, "model_id": TTS_MODEL,
              "voice_settings": {
                  "stability": voice_cfg.get("stability", 0.45),
                  "similarity_boost": voice_cfg.get("similarity_boost", 0.8)
              }},
    )
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


def sfx(name: str) -> Path:
    """Local file wins (deterministic). If missing, generate once and keep it."""
    for suffix in (".wav", ".mp3", ".m4a", ".ogg"):
        path = SFX_DIR / f"{name}{suffix}"
        if path.exists():
            return path
    path = SFX_DIR / f"{name}.mp3"
        
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print(f"[AudioLayer] Warning: ELEVENLABS_API_KEY missing. Missing SFX: {name}")
        return None
        
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    r = requests.post(
        f"{API}/sound-generation", headers=_headers(), timeout=60,
        json={"text": SFX_PROMPTS.get(name, "clean cinematic sound effect"), "duration_seconds": 1.0},
    )
    r.raise_for_status()
    path.write_bytes(r.content)
    return path


def _duration(path: Path) -> float:
    if not path or not path.exists():
        return 0.0
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]
    )
    return float(out)


def _mix_items(items: list[tuple[Path, float, float, float]], out: Path, duration: float = DURATION) -> Path:
    """Mix audio items into the timed timeline."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if not items:
        return None

    cmd = ["ffmpeg", "-y"]
    for p, *_ in items:
        cmd += ["-i", str(p)]

    chains = []
    for i, (_, start, gain, tempo) in enumerate(items):
        f = ([f"atempo={tempo:.3f}"] if tempo > 1.0 else []) + [f"volume={gain}", f"adelay={int(start * 1000)}:all=1"]
        chains.append(f"[{i}:a]{','.join(f)}[a{i}]")
    ins = "".join(f"[a{i}]" for i in range(len(items)))
    chains.append(
        f"{ins}amix=inputs={len(items)}:normalize=0:dropout_transition=0,apad,"
        f"atrim=0:{duration},alimiter=limit=0.95[out]"
    )
    cmd += ["-filter_complex", ";".join(chains), "-map", "[out]", "-ar", "44100", str(out)]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return out


def build_dynamic_cues(storyboard_spec: dict) -> dict:
    """Builds per-scene voiceover windows and SFX cue timestamps dynamically from storyboard."""
    scenes = storyboard_spec.get("scenes", [])
    vo_cues = []
    sfx_cues = []
    elapsed = 0.0

    for idx, scene in enumerate(scenes):
        dur = float(scene.get("duration_seconds") or scene.get("duration") or 4.0)
        vo_text = scene.get("voiceover", "").strip()
        if vo_text:
            vo_cues.append((f"VO_{idx+1}", round(elapsed + 0.15, 2), round(elapsed + dur - 0.15, 2), vo_text))

        # Add transition / entry SFX
        if idx == 0:
            sfx_cues.append(("whoosh", round(elapsed, 2)))
            sfx_cues.append(("pop", round(elapsed + dur * 0.7, 2)))
        elif idx == len(scenes) - 1:
            sfx_cues.append(("whoosh", round(elapsed, 2)))
            sfx_cues.append(("ding", round(elapsed + dur * 0.5, 2)))
        else:
            sfx_cues.append(("pop", round(elapsed, 2)))
            if dur > 3.0:
                sfx_cues.append(("tick", round(elapsed + dur * 0.5, 2)))

        elapsed += dur

    return {
        "total_duration": round(elapsed, 2),
        "vo": vo_cues,
        "sfx": sfx_cues
    }


def build_dynamic_track(storyboard_spec: dict, out: Path, voice_override: str = None) -> Path:
    """Builds a dynamic voiceover and SFX audio track matching the flexible storyboard."""
    voice_style = storyboard_spec.get("voice_style", "fast_confident")
    cues = build_dynamic_cues(storyboard_spec)
    items = []

    for name, start, end, vo_text in cues["vo"]:
        p = tts(vo_text, voice_style=voice_style, voice_id_override=voice_override)
        if not p:
            continue
        d = _duration(p)
        window = end - start
        tempo = 1.0
        if d > window:
            tempo = min(d / window, MAX_SPEEDUP)
        items.append((p, start, VO_GAIN, tempo))

    for name, start in cues["sfx"]:
        p = sfx(name)
        if p:
            items.append((p, start, SFX_GAIN, 1.0))

    total_dur = cues.get("total_duration", DURATION)
    return _mix_items(items, out, duration=total_dur)


# ---------------------------------------------------------------- the mixer
def build_track(template: str, data: dict, out: Path) -> Path:
    cues = CUES[template]
    items = []  # (path, start_s, gain, tempo)

    for field, start, end in cues["vo"]:
        p = tts(data[field])
        if not p:
            continue
        d, window = _duration(p), end - start
        tempo = 1.0
        if d > window:
            tempo = d / window
            if tempo > MAX_SPEEDUP:
                raise VoiceTooLong(f"{field} is {d:.1f}s but its scene window is {window:.1f}s; shorten the line")
        items.append((p, start, VO_GAIN, tempo))

    for name, start in cues["sfx"]:
        p = sfx(name)
        if p:
            items.append((p, start, SFX_GAIN, 1.0))

    return _mix_items(items, out)


def mix_existing_voiceover(voiceover: Path, template: str, out: Path, *, include_sfx: bool = True) -> Path:
    """Add the legacy cue layer to a supplied full voiceover file.

    ``programmatic_pipeline.py --audio`` historically bypassed ``build_track``
    completely, which meant a valid voiceover export had no SFX. This adapter
    keeps that command compatible while giving it the same transition cues as
    the generated per-scene path.
    """
    voiceover = Path(voiceover)
    if not voiceover.is_file():
        raise FileNotFoundError(f"Voiceover file not found: {voiceover}")
    items = [(voiceover, 0.0, VO_GAIN, 1.0)]
    if include_sfx:
        for name, start in CUES[template]["sfx"]:
            path = sfx(name)
            if path:
                items.append((path, start, SFX_GAIN, 1.0))
    return _mix_items(items, out)
