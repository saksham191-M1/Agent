"""Seekable browser frames -> native-resolution H.264, with one shared audio/video timeline."""
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable

from .models import ASPECTS, StudioError, narration_word_budget, timeline
from .editing import RENDERER_VERSION, shot_plan
from .providers import narration_settings, synthesize
from .sound_design import SFX_GAIN, find_music, get_sfx, sfx_cues

Progress = Callable[[float, str], None]


class RenderCancelled(StudioError):
    pass


def check_cancel(cancel: threading.Event) -> None:
    if cancel.is_set():
        raise RenderCancelled("Render cancelled. Your storyboard is saved; no incomplete export was published.")


def probe_media(path: Path, *, ffprobe_executable=None) -> dict:
    try:
        result = subprocess.run(
            [ffprobe_executable or os.getenv("FFPROBE_PATH", "ffprobe"), "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate", "-of", "json", str(path)],
            capture_output=True, check=True, timeout=30,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        raise StudioError("Media could not be verified. Install FFmpeg/ffprobe and check the source file.") from None


def check_export(path: Path, width: int, height: int, fps: int, duration: float, audio_expected: bool, *, ffprobe_executable=None) -> dict:
    info = probe_media(path, ffprobe_executable=ffprobe_executable)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    if (video.get("width"), video.get("height")) != (width, height) or video.get("codec_name") != "h264":
        raise StudioError("The rendered video failed its resolution/codec check. It was not published.")
    try:
        num, den = map(float, video["r_frame_rate"].split("/"))
        actual_fps = num / den
        actual_duration = float(info["format"]["duration"])
    except (KeyError, ValueError, ZeroDivisionError):
        raise StudioError("The rendered video has invalid timing metadata.") from None
    if abs(actual_fps - fps) > 0.01 or abs(actual_duration - duration) > max(0.12, 2 / fps):
        raise StudioError("The rendered video failed its frame-rate/duration check. It was not published.")
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    if audio_expected != has_audio:
        raise StudioError("The export's audio does not match the selected narration/SFX settings. It was not published.")
    return {"width": width, "height": height, "fps": fps, "duration": actual_duration, "audio": has_audio}


def build_audio(project: dict, directory: Path, cache: Path, progress: Progress, cancel: threading.Event,
                *, include_sfx: bool = False, narrated: bool = True) -> Path:
    scenes = timeline(project["scenes"])
    # Validate all lines before any paid request.
    for s in scenes if narrated else []:
        budget = narration_word_budget(s["duration"])
        if not s["narration"] or len(s["narration"].split()) > budget:
            raise StudioError(f"Shorten the {s['kind']} voiceover to about {budget} words so it fits its scene.")
    inputs, filters = [], []

    def add_input(path: Path, *, loop: bool = False) -> int:
        index = len(inputs)
        inputs.append((path, loop))
        return index

    def delayed_filter(index: int, start: float, gain: float, *, trim_edges: bool = False,
                       tempo: float = 1.0) -> str:
        steps = ["aresample=48000"]
        if trim_edges:
            # TTS providers commonly add a small lead/trail pad.  Only the
            # edges are removed; pauses inside a sentence are preserved.
            steps.append(
                "silenceremove=start_periods=1:start_duration=0.06:start_threshold=-45dB:"
                "stop_periods=1:stop_duration=0.08:stop_threshold=-45dB"
            )
        if tempo > 1.0:
            steps.append(f"atempo={tempo:.6f}")
        steps.extend([f"volume={gain:.3f}", f"adelay={round(start * 1000)}:all=1"])
        return f"[{index}:a]{','.join(steps)}[a{index}]"

    for i, scene in enumerate(scenes if narrated else []):
        check_cancel(cancel)
        progress(.03 + i * .035, f"Preparing narration {i + 1}/{len(scenes)} (ElevenLabs)")
        path = synthesize(scene["narration"], cache)
        d = float(probe_media(path)["format"]["duration"])
        window = scene["duration"] - .3
        speed = max(1.0, d / window)
        if speed > 1.12 or d <= 0:
            raise StudioError(f"The {scene['kind']} voiceover lasts {d:.1f}s; its window is {window:.1f}s. Shorten that line or give the scene more time.")
        input_index = add_input(path)
        filters.append(delayed_filter(input_index, scene["start"] + .12, 1.0, trim_edges=True, tempo=speed))

    if include_sfx:
        progress(.17, "Adding motion SFX and optional local music bed")
        cues = sfx_cues(project["scenes"])
        (directory / "sound_cues.json").write_text(json.dumps(
            [{"name": name, "start": start} for name, start in cues], indent=2), encoding="utf-8")
        for name, start in cues:
            check_cancel(cancel)
            path = get_sfx(name, cache)
            input_index = add_input(path)
            filters.append(delayed_filter(input_index, start, SFX_GAIN[name] * (1 if narrated else 1.4)))

        music = find_music()
        if music:
            input_index = add_input(music, loop=True)
            duration = project["brief"]["duration"]
            fade_start = max(0.0, duration - .8)
            filters.append(
                f"[{input_index}:a]aresample=48000,atrim=0:{duration},asetpts=PTS-STARTPTS,"
                 f"volume={0.075 if narrated else 0.18},afade=t=in:st=0:d=.8,afade=t=out:st={fade_start:.3f}:d=.8[a{input_index}]"
             )
    check_cancel(cancel)
    if not inputs:
        raise StudioError("Choose narration or motion sound design before building an audio mix.")
    filters.append("".join(f"[a{i}]" for i in range(len(inputs))) +
                   f"amix=inputs={len(inputs)}:normalize=0:dropout_transition=0,apad,atrim=0:{project['brief']['duration']},"
                   "alimiter=limit=0.95:level=0:latency=1[out]")
    out = directory / ("narration.wav" if narrated else "sound_design.wav")
    try:
        input_args = []
        for path, loop in inputs:
            if loop:
                input_args.extend(["-stream_loop", "-1"])
            input_args.extend(["-i", str(path)])
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *input_args, "-filter_complex", ";".join(filters),
                        "-map", "[out]", "-ar", "48000", "-ac", "2", str(out)],
                       check=True, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        raise StudioError("Audio mixing failed. Your storyboard and cached sound files are preserved.") from None
    return out


def _image_uri(path: str | None) -> str | None:
    if not path:
        return None
    return "data:image/png;base64," + base64.b64encode(Path(path).read_bytes()).decode("ascii")


def serve_video(route, path: Path):
    """Honor Chromium's byte-range seeks for a single local, normalized MP4."""
    body = path.read_bytes()
    size = len(body)
    headers = {"Accept-Ranges": "bytes", "Access-Control-Allow-Origin": "*"}
    requested = route.request.headers.get("range")
    if requested:
        match = re.fullmatch(r"bytes=(\d+)-(\d*)", requested)
        if not match:
            route.fulfill(status=416, headers={"Content-Range": f"bytes */{size}"}, body=b"")
            return
        start = int(match[1])
        end = min(int(match[2]) if match[2] else size - 1, size - 1)
        if start > end:
            route.fulfill(status=416, headers={"Content-Range": f"bytes */{size}"}, body=b"")
            return
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        route.fulfill(status=206, headers=headers, body=body[start:end + 1], content_type="video/mp4")
    else:
        route.fulfill(status=200, headers=headers, body=body, content_type="video/mp4")


def build_document(project: dict, narrated: bool) -> str:
    labels = {"English": ["Introducing", "The difference", "Made for you", "Discover more"],
              "Hindi": ["परिचय", "खास बात", "आपके लिए", "और जानें"],
              "Hinglish": ["Meet your next", "Kya hai khaas", "Aapke liye", "Explore karein"]}
    data = {"brief": project["brief"], "scenes": timeline(project["scenes"]), "narrated": narrated,
            "logo": _image_uri(project.get("assets", {}).get("logo")),
            "screenshot": _image_uri(project.get("assets", {}).get("screenshot")),
            "labels": labels[project["brief"]["language"]],
            "look": (project.get("creative") or {}).get("look", "glow")}
    data["scene_images"] = [_image_uri(project.get("assets", {}).get(f"scene_{i}")) for i in range(1, 5)]
    data["shots"] = shot_plan(project["scenes"])
    demo = project.get("assets", {}).get("demo")
    # Normalized footage is copied into the render folder. Relative media keeps
    # the saved composition replayable without embedding a large video in JSON.
    data["demo"] = "demo.mp4" if demo else None
    # JSON is data, never HTML. Escape script delimiters even for user-supplied copy.
    safe_json = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return (Path(__file__).parent / "templates" / "film.html").read_text(encoding="utf-8").replace("__PROJECT_JSON__", safe_json)


def write_script(project: dict, directory: Path) -> dict:
    def stamp(seconds):
        milliseconds = round(seconds * 1000)
        hours, milliseconds = divmod(milliseconds, 3600000)
        minutes, milliseconds = divmod(milliseconds, 60000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    lines, captions = [], []
    for index, scene in enumerate(timeline(project["scenes"]), 1):
        lines.append(f"{scene['start']:g}–{scene['end']:g}s | {scene['kind']}\n{scene['narration']}")
        if scene["narration"]:
            captions.append(f"{index}\n{stamp(scene['start'] + .2)} --> {stamp(scene['end'] - .2)}\n{scene['narration']}")
    script, srt = directory / "voiceover.txt", directory / "captions.srt"
    script.write_text(f"{project['name']} — voiceover script\n\n" + "\n\n".join(lines) + "\n", encoding="utf-8")
    srt.write_text("\n\n".join(captions) + "\n", encoding="utf-8")
    return {"script": str(script), "captions": str(srt)}


def render_video(project: dict, directory: Path, quality: str, narrated: bool, cache: Path,
                 progress: Progress, cancel: threading.Event, *, dimensions=None, frame_rate=None,
                 include_sfx: bool = False) -> dict:
    if quality not in ("draft", "final"):
        raise StudioError("Choose Draft preview or Final export.")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise StudioError("FFmpeg and ffprobe must be on PATH before rendering. See the README setup steps.")
    from playwright.sync_api import sync_playwright

    width, height = ASPECTS[project["brief"]["aspect"]]
    if quality == "draft":
        width, height = width // 3, height // 3
    width, height = dimensions or (width, height)
    fps = frame_rate or (24 if quality == "draft" else 30)
    duration = project["brief"]["duration"]
    directory.mkdir(parents=True, exist_ok=True)
    check_cancel(cancel)
    audio = (build_audio(project, directory, cache, progress, cancel,
                         include_sfx=bool(include_sfx), narrated=bool(narrated))
             if narrated or include_sfx else None)
    demo = project.get("assets", {}).get("demo")
    if demo:
        shutil.copyfile(demo, directory / "demo.mp4")
    document = build_document(project, narrated)
    # Also save the exact standalone visual composition used for this render.
    (directory / "composition.html").write_text(document, encoding="utf-8")
    out, poster = directory / "video.mp4", directory / "poster.jpg"
    command = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-vcodec", "mjpeg",
               "-framerate", str(fps), "-i", "pipe:0"]
    if audio:
        command += ["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"]
    else:
        command += ["-an"]
    command += ["-c:v", "libx264", "-preset", "fast", "-crf", "18" if quality == "final" else "24",
                "-pix_fmt", "yuv420p", "-t", str(duration), "-movflags", "+faststart", str(out)]
    process = None
    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(headless=True)
            except Exception:
                raise StudioError("Chromium is unavailable. Run: python -m playwright install chromium") from None
            try:
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1,
                                        color_scheme="dark", reduced_motion="no-preference")
                page.set_default_timeout(20000)
                # Only the copied local footage is allowed; never load remote product code.
                def local_media(route):
                    if demo and route.request.url == "https://studio.local/demo.mp4":
                        serve_video(route, directory / "demo.mp4")
                    else:
                        route.abort()
                page.route("**/*", local_media)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                # set_content has an about:blank base; this base is intercepted
                # above and works identically to relative media in the saved HTML.
                browser_document = document.replace('<head>', '<head><base href="https://studio.local/">', 1)
                page.set_content(browser_document, wait_until="load")
                page.evaluate("window.ready")
                page.evaluate("window.renderAt(1.0)")
                page.screenshot(path=str(poster), type="jpeg", quality=94, animations="disabled")
                if errors:
                    raise StudioError("The visual composition failed to initialize. No video was published.")
                progress(.18, f"Rendering {width} × {height} at {fps} fps, frame by frame")
                count = int(round(duration * fps))
                with (directory / "encoder.log").open("wb") as log:
                    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
                    for frame in range(count):
                        check_cancel(cancel)
                        page.evaluate("window.renderAt", frame / fps)
                        image = page.screenshot(type="jpeg", quality=95 if quality == "final" else 86,
                                                animations="disabled", timeout=20000)
                        process.stdin.write(image)
                        if frame % max(1, fps // 2) == 0:
                            progress(.18 + .74 * frame / count, f"{quality.title()} · frame {frame + 1}/{count}")
                    process.stdin.close()
                    if process.wait(timeout=120) != 0:
                        raise StudioError("FFmpeg encoding failed. Check the render's encoder.log; no export was published.")
                if errors:
                    raise StudioError("A visual error occurred during rendering. No export was published.")
            finally:
                browser.close()
        check_cancel(cancel)
        progress(.95, "Verifying duration, dimensions, frame rate, and audio")
        metadata = check_export(out, width, height, fps, duration, bool(audio))
        return {"video": str(out), "poster": str(poster), "metadata": metadata,
                 "audio": str(audio) if audio else None,
                 "sound_cues": str(directory / "sound_cues.json") if include_sfx else None,
                 "sfx": bool(audio and include_sfx),
                 "narration_settings": narration_settings() if narrated else None,
                 "renderer_version": RENDERER_VERSION,
                 "visual_source": "screen_recording" if demo else "product_images" if any(
                     key == "screenshot" or key.startswith("scene_") for key in project.get("assets", {})) else "typography",
                **write_script(project, directory)}
    except (BrokenPipeError, subprocess.TimeoutExpired, OSError):
        raise StudioError("The renderer or encoder stopped unexpectedly. Check FFmpeg and available disk space.") from None
    finally:
        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=10)
            if process.stdin and not process.stdin.closed:
                try:
                    process.stdin.close()
                except OSError:
                    pass  # Preserve the original cancellation/error after killing the encoder.
