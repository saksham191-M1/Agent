"""Validated Jarvis projects -> local Remotion composition -> checked MP4."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from .models import ASPECTS, StudioError, timeline
from .providers import narration_settings
from .render import RenderCancelled, build_audio, check_cancel, check_export, write_script

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTION_RENDERER_VERSION = "remotion-project-3"
_runtime_cache: dict = {}


def remotion_root() -> Path:
    root = Path(os.getenv("STUDIO_REMOTION_ROOT", "remotion-swiggy")).expanduser()
    return (root if root.is_absolute() else PROJECT_ROOT / root).resolve()


def _runtime_env() -> dict:
    env = os.environ.copy()
    if env.get("REMOTION_LD_LIBRARY_PATH"):
        env["LD_LIBRARY_PATH"] = env["REMOTION_LD_LIBRARY_PATH"]
    if not env.get("REMOTION_BROWSER_EXECUTABLE"):
        # A native Playwright Chromium is also a usable Remotion browser. This
        # avoids trying a WSL binary from a Windows Python interpreter.
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = Path(pw.chromium.executable_path)
                if browser.is_file():
                    env["REMOTION_BROWSER_EXECUTABLE"] = str(browser)
        except Exception:
            pass
    return env


def remotion_status() -> dict:
    """Check native Node, esbuild, encoders and a real headless browser launch."""
    root = remotion_root()
    node = os.getenv("STUDIO_NODE_PATH") or shutil.which("node")
    if not node or not (root / "scripts" / "check-runtime.mjs").is_file():
        return {"ready": False, "reason": "Install Node and run npm ci in remotion-swiggy."}
    env = _runtime_env()
    key = (str(root), node, env.get("REMOTION_BROWSER_EXECUTABLE"), env.get("LD_LIBRARY_PATH"), env.get("FFMPEG_PATH"), env.get("FFPROBE_PATH"))
    cached = _runtime_cache.get(key)
    if cached and time.monotonic() - cached[0] < 20:
        return cached[1]
    try:
        result = subprocess.run([node, str(root / "scripts" / "check-runtime.mjs")], cwd=root, env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=40)
        status = json.loads(result.stdout)
        if not isinstance(status, dict) or not isinstance(status.get("ready"), bool) or (result.returncode and status["ready"]):
            raise ValueError("Invalid runtime status")
    except (OSError, subprocess.SubprocessError, ValueError):
        status = {"ready": False, "reason": "Remotion runtime check failed; check Node, browser and FFmpeg setup."}
    _runtime_cache[key] = (time.monotonic(), status)
    return status


def remotion_available() -> bool:
    return bool(remotion_status().get("ready"))


def renderer_version() -> str:
    """Invalidate cached daily exports when composition/renderer code changes."""
    root = remotion_root()
    files = [root / "project-entry.tsx", root / "package-lock.json"]
    files.extend(sorted((root / "engine").rglob("*.ts*")))
    files.extend(sorted((root / "scripts").glob("*")))
    digest = hashlib.sha256()
    for file in files:
        if file.is_file():
            digest.update(str(file.relative_to(root)).encode())
            digest.update(file.read_bytes())
    return f"{REMOTION_RENDERER_VERSION}:{digest.hexdigest()[:16]}"


def _manifest(project: dict, directory: Path, quality: str, audio: Path | None, *, narrated=False) -> Path:
    brief = project["brief"]
    assets = {}
    for key, value in (project.get("assets") or {}).items():
        if not value or not Path(value).is_file():
            raise StudioError(f"The project's {key} asset is missing. Re-upload it before rendering.")
        assets[key] = str(Path(value).resolve())
    payload = {
        "id": f"{project['id']}-{directory.name}", "name": project["name"], "quality": quality,
        "format": brief["aspect"], "fps": 24 if quality == "draft" else 30, "durationSec": brief["duration"],
        "narrated": bool(narrated), "demoDuration": project.get("media", {}).get("demo", {}).get("duration"),
        "look": project.get("creative", {}).get("look", "glow"),
        "brief": {key: brief[key] for key in ("name", "description", "audience", "problem", "benefits", "cta", "url", "color", "template", "tone", "language")},
        "scenes": [{"id": f"S{index}", **scene} for index, scene in enumerate(timeline(project["scenes"]), 1)],
        "assets": assets, "audio": str(audio.resolve()) if audio else None,
    }
    path = directory / "remotion-project.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _stop_tree(process) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=15)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=10)


def render_remotion(project: dict, directory: Path, quality: str, narrated: bool, cache: Path,
                    progress, cancel, *, include_sfx: bool = False) -> dict:
    if quality not in ("draft", "final"):
        raise StudioError("Choose Draft preview or Final export.")
    runtime = remotion_status()
    if not runtime.get("ready"):
        raise StudioError(runtime.get("reason", "Remotion is unavailable."))
    root = remotion_root()
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    check_cancel(cancel)
    # Validate assets before making a narration request.
    _manifest(project, directory, quality, None, narrated=narrated)
    audio = build_audio(project, directory, cache, progress, cancel, include_sfx=bool(include_sfx), narrated=bool(narrated)) if narrated or include_sfx else None
    manifest = _manifest(project, directory, quality, audio, narrated=narrated)
    script_files = write_script(project, directory)
    output, poster = directory / "video.mp4", directory / "poster.jpg"
    command = [os.getenv("STUDIO_NODE_PATH") or shutil.which("node"), "--import", "tsx", str(root / "scripts" / "render-project.ts"), str(manifest), str(output)]
    progress(.18, "Rendering the validated project with Remotion")
    process = None
    timeout = float(os.getenv("STUDIO_REMOTION_TIMEOUT", "1800"))
    if not 10 <= timeout <= 7200:
        raise StudioError("STUDIO_REMOTION_TIMEOUT must be between 10 and 7200 seconds.")
    deadline = time.monotonic() + timeout
    try:
        with (directory / "encoder.log").open("wb") as log:
            process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                                       env=_runtime_env(), start_new_session=os.name != "nt")
            while process.poll() is None:
                if cancel.is_set() or time.monotonic() > deadline:
                    (directory / "cancel.requested").touch()
                    try:
                        process.wait(timeout=12)
                    except subprocess.TimeoutExpired:
                        _stop_tree(process)
                    check_cancel(cancel)
                    raise StudioError("Remotion exceeded the render timeout. Retry a draft; see encoder.log.")
                time.sleep(.2)
        check_cancel(cancel)
        if process.returncode != 0:
            raise StudioError("Remotion rendering or export QA failed. See this render's encoder.log; the storyboard is saved.")
        qa = json.loads((directory / "qa-report.json").read_text(encoding="utf-8"))
        if not qa.get("passed") or not qa.get("gates") or not all(qa["gates"].values()) or not poster.is_file():
            raise StudioError("The Remotion export failed verification; it was not published.")
        width, height = ASPECTS[project["brief"]["aspect"]]
        if quality == "draft":
            width, height = width // 3, height // 3
        metadata = check_export(output, width, height, 24 if quality == "draft" else 30,
                                project["brief"]["duration"], bool(audio), ffprobe_executable=runtime["ffprobe"])
        return {"video": str(output), "poster": str(poster), "metadata": metadata, "audio": str(audio) if audio else None,
                "sound_cues": str(directory / "sound_cues.json") if include_sfx else None, "sfx": bool(audio and include_sfx),
                "narration_settings": narration_settings() if narrated else None, "renderer_version": renderer_version(),
                "qa_report": str(directory / "qa-report.json"), "manifest": str(manifest),
                "visual_source": "screen_recording" if project.get("assets", {}).get("demo") else "product_images" if any(key == "screenshot" or key.startswith("scene_") for key in project.get("assets", {})) else "typography", **script_files}
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        raise StudioError("Remotion stopped or returned incomplete verification data. Check encoder.log and retry.") from None
    finally:
        if process and process.poll() is None:
            _stop_tree(process)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    status = remotion_status()
    print(json.dumps(status, ensure_ascii=False, indent=2))
    raise SystemExit(0 if status.get("ready") else 1)
