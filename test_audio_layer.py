"""
test_audio_layer.py
Tests audio_layer.build_track() WITHOUT calling ElevenLabs.

How: audio_layer.tts / audio_layer.sfx are replaced with fakes that make pure sine tones
(each voice line and each SFX type gets its own frequency). The REAL ffmpeg mix then runs,
and the output is analysed per cue frequency to check:
  * total length is 15s, peak does not clip
  * every cue starts at its scheduled time (within 40 ms)
  * VO level vs SFX level matches VO_GAIN / SFX_GAIN
  * a slightly-long VO line is sped up and still ends inside its window
  * a far-too-long VO line raises VoiceTooLong

Run from the JARVIS root:   pip install numpy
    python test_audio_layer.py                 # all templates
    python test_audio_layer.py --template iphone_showcase_master
    python test_audio_layer.py --loud          # VO near full scale: checks the limiter
    python test_audio_layer.py --video output/kora_iphone_showcase_master.mp4   # ear check on real video
Mixes are saved to output/test_audio/ so you can listen to them.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
# audio_layer may skip mixing when no key is set; fake keys keep it on the real code path.
os.environ.setdefault("ELEVENLABS_API_KEY", "fake-key-for-tests")
os.environ.setdefault("ELEVENLABS_VOICE_ID", "fake-voice")
import audio_layer as al  # noqa: E402

SR = 44100
OUT_DIR = Path("output/test_audio")
SFX_FREQS = {"whoosh": 1500, "pop": 2300, "ding": 3100}
SFX_DURS = {"whoosh": 0.6, "pop": 0.12, "ding": 0.5}
FAKE_AMP = 0.5
ONSET_TOL = 0.040   # seconds
LEVEL_TOL = 0.50    # +/- 50 %

N = int(0.04 * SR)
HOP = int(0.005 * SR)
WIN = np.hanning(N)

# (name, {vo_index: duration factor vs window}, expect VoiceTooLong)
SCENARIOS = [
    ("nominal", {}, False),
    ("stretch", {2: 1.10}, False),    # 10% too long -> must be sped up, still fits
    ("overlong", {3: 1.30}, True),    # 30% too long -> must raise
]
DEFAULT_FACTOR = 0.8


# ------------------------------------------------------------------ fakes
def make_tone(path: Path, freq: float, dur: float, amp: float) -> None:
    fade = 0.01
    # ffmpeg 'sine' filter outputs at ~0.21875 amplitude (-13.2 dB). Compensate here.
    real_amp = amp / 0.21875
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={dur}:sample_rate={SR}",
         "-af", f"volume={real_amp},afade=t=in:d={fade},afade=t=out:st={max(dur - fade, 0)}:d={fade}", str(path)],
        check=True,
    )


def install_fakes(plan: dict, tmp: Path, vo_amp: float) -> None:
    def fake_tts(text: str) -> Path:
        freq, dur = plan[text]
        p = tmp / f"vo_{freq}_{dur:.3f}.wav"
        if not p.exists():
            make_tone(p, freq, dur, vo_amp)
        return p

    def fake_sfx(name: str) -> Path:
        p = tmp / f"sfx_{name}.wav"
        if not p.exists():
            make_tone(p, SFX_FREQS[name], SFX_DURS[name], FAKE_AMP)
        return p

    al.tts, al.sfx = fake_tts, fake_sfx


# --------------------------------------------------------------- analysis
def load_mono(path: Path) -> np.ndarray:
    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype="<f4")


def amp_track(x: np.ndarray, freq: float) -> np.ndarray:
    """Amplitude of a single frequency over time (sliding Hann-windowed DFT bin)."""
    e = (WIN * np.exp(-2j * np.pi * freq * np.arange(N) / SR)).astype(np.complex64)
    frames = np.lib.stride_tricks.sliding_window_view(x, N)[::HOP]
    return 2 * np.abs(frames @ e) / WIN.sum()


class Report:
    def __init__(self):
        self.failures = 0

    def check(self, ok: bool, label: str, detail: str) -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {detail}")
        if not ok:
            self.failures += 1


def check_cue(rep, x, cache, freq, start, expected_amp, label, window_end=None, loud=False):
    if freq not in cache:
        cache[freq] = amp_track(x, freq)
    a = cache[freq]
    t = (np.arange(len(a)) * HOP + N / 2) / SR
    thr = 0.3 * expected_amp

    idx = np.where((t >= start - 0.10) & (t <= start + 0.30) & (a > thr))[0]
    if len(idx) == 0:
        rep.check(False, f"{label} onset", f"not found near {start:.2f}s")
        return
    err = t[idx[0]] - start
    rep.check(abs(err) <= ONSET_TOL, f"{label} onset", f"scheduled {start:.2f}s, measured {err * 1000:+.0f} ms")

    if not loud:
        seg = a[(t >= start) & (t <= start + 0.5)]
        ratio = seg.max() / expected_amp
        rep.check(abs(ratio - 1) <= LEVEL_TOL, f"{label} level", f"{ratio * 100:.0f}% of expected")

    if window_end is not None:
        active = np.where((t >= start) & (t <= window_end + 1.0) & (a > thr))[0]
        end_est = t[active[-1]] if len(active) else start
        rep.check(end_est <= window_end + 0.05, f"{label} ends in window", f"ends ~{end_est:.2f}s, window closes {window_end:.2f}s")


# --------------------------------------------------------------- scenarios
def run_scenario(template, name, overrides, expect_error, loud, tmp, rep) -> Path | None:
    print(f"\n{template} / {name}")
    cues = al.CUES[template]
    vo = cues["vo"]
    vo_amp = 0.95 if loud else FAKE_AMP

    plan, data, vo_freqs = {}, {}, {}
    for i, (field, start, end) in enumerate(vo):
        factor = overrides.get(i % len(vo), DEFAULT_FACTOR) if overrides else DEFAULT_FACTOR
        text = f"{field}:{name}"
        freq = 300 + 200 * i
        plan[text] = (freq, (end - start) * factor)
        data[field] = text
        vo_freqs[field] = freq

    sub = tmp / name
    sub.mkdir(exist_ok=True)
    install_fakes(plan, sub, vo_amp)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{template}_{name}.wav"
    try:
        result = al.build_track(template, data, out)
    except al.VoiceTooLong as exc:
        rep.check(expect_error, "VoiceTooLong raised", str(exc))
        return None
    if expect_error:
        rep.check(False, "VoiceTooLong raised", "build_track accepted an over-long line")
        return None
    if result is None or not Path(result).exists():
        rep.check(False, "build_track output", "returned None / no file (is the key-skip path triggering?)")
        return None

    x = load_mono(Path(result))
    rep.check(abs(len(x) / SR - al.DURATION) <= 0.02, "length", f"{len(x) / SR:.3f}s (want {al.DURATION}s)")
    rep.check(float(np.abs(x).max()) <= 0.96, "peak", f"{np.abs(x).max():.3f} (limit 0.95)")

    cache = {}
    for field, start, end in vo:
        check_cue(rep, x, cache, vo_freqs[field], start, vo_amp * al.VO_GAIN, field, window_end=end, loud=loud)
    for sfx_name, start in cues["sfx"]:
        check_cue(rep, x, cache, SFX_FREQS[sfx_name], start, FAKE_AMP * al.SFX_GAIN, f"sfx {sfx_name}@{start:.1f}", loud=loud)
    return Path(result)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", choices=list(al.CUES))
    ap.add_argument("--loud", action="store_true", help="VO near full scale to exercise the limiter")
    ap.add_argument("--video", type=Path, help="mux the nominal test mix onto this video for an ear check")
    args = ap.parse_args()

    rep = Report()
    nominal_mix = None
    with tempfile.TemporaryDirectory() as td:
        for template in ([args.template] if args.template else list(al.CUES)):
            for name, overrides, expect_error in SCENARIOS:
                mix = run_scenario(template, name, overrides, expect_error, args.loud, Path(td), rep)
                if name == "nominal" and mix and nominal_mix is None:
                    nominal_mix = mix

    if args.video and nominal_mix:
        out = OUT_DIR / "ear_check.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(args.video), "-i", str(nominal_mix),
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", str(out)],
            check=True,
        )
        print(f"\nEar check video: {out}  (low beeps = voice lines, high beeps = SFX)")

    print(f"\n{'ALL CHECKS PASSED' if rep.failures == 0 else str(rep.failures) + ' CHECK(S) FAILED'}")
    print(f"Listen to the mixes in {OUT_DIR}/")
    sys.exit(1 if rep.failures else 0)


if __name__ == "__main__":
    main()
