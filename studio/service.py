"""Local projects, atomic persistence, explicit jobs, and the UI-facing studio API."""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import threading
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from .assets import normalize_image as _normalize_image
from .assets import normalize_video
from .editing import RENDERER_VERSION
from .catalog import ProductCatalog
from .intake import PromptBrief, parse_ad_prompt
from .creative import duplicate_reason, rotated_brief, select_plan, signature, variant_storyboard
from .locking import FileLock, replace_file
from .models import ASPECTS, StudioError, project_rows, template_storyboard, text, validate_brief, validate_scenes
from .providers import GROQ_DEFAULT_MODEL, generate_storyboard, narration_settings, suggest_brief_fields
from .strategy import deterministic_strategy
from .render import RenderCancelled, check_export, render_video
from .remotion_backend import REMOTION_RENDERER_VERSION, render_remotion, remotion_available, remotion_status, renderer_version

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _progress(callback, amount, message):
    if callback:
        callback(amount, message)


class StudioService:
    def __init__(self, root: str | Path | None = None, *, load_environment: bool = True):
        if load_environment:
            load_dotenv(PROJECT_ROOT / ".env", override=False)
        self.renderer_mode = os.getenv("STUDIO_RENDERER", "auto" if load_environment else "python").strip().casefold()
        if self.renderer_mode not in {"auto", "python", "remotion"}:
            raise StudioError("STUDIO_RENDERER must be auto, python, or remotion.")
        self.root = Path(root or PROJECT_ROOT / "output" / "studio").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._render_lock = threading.Lock()
        self._cancels: dict[str, threading.Event] = {}
        self.catalog = ProductCatalog(self.root)
        self._campaign_lock = threading.RLock()
        # Do not mislabel another live process's render as an interrupted job.
        recovery = FileLock(self.root / ".render.lock", "Another render is active")
        try:
            recovery.acquire()
        except StudioError:
            return
        try:
            for path in self.root.glob("*/project.json"):
                try:
                    project = json.loads(path.read_text(encoding="utf-8"))
                    if project.get("status") == "rendering":
                        project.update(status="failed", error="The app stopped during rendering. Your storyboard is saved; render again.")
                        self._save(project)
                except (OSError, ValueError, StudioError, KeyError):
                    continue
        finally:
            recovery.release()

    def capabilities(self) -> dict:
        browser = False
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = Path(p.chromium.executable_path).is_file()
        except Exception:
            pass
        runtime = remotion_status()
        return {"ffmpeg": bool(shutil.which("ffmpeg")), "ffprobe": bool(shutil.which("ffprobe")), "browser": browser,
                "remotion": bool(runtime.get("ready")), "remotion_reason": runtime.get("reason", ""), "renderer": self._renderer_version(),
                "ai_ready": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL")),
                "groq_ready": bool(os.getenv("GROQ_API_KEY", "").strip()),
                "voice_ready": bool(os.getenv("ELEVENLABS_API_KEY")), "model": os.getenv("GEMINI_MODEL", ""),
                "groq_model": os.getenv("GROQ_MODEL", "").strip() or GROQ_DEFAULT_MODEL}

    def _renderer_backend(self):
        if self.renderer_mode == "python":
            return render_video, RENDERER_VERSION
        if self.renderer_mode == "remotion":
            if not remotion_available():
                raise StudioError(remotion_status().get("reason") or "Remotion is selected but its Node project or browser runtime is unavailable.")
            return render_remotion, renderer_version()
        if remotion_available():
            return render_remotion, renderer_version()
        return render_video, RENDERER_VERSION

    def _renderer_version(self) -> str:
        try:
            return self._renderer_backend()[1]
        except StudioError:
            return REMOTION_RENDERER_VERSION if self.renderer_mode == "remotion" else RENDERER_VERSION

    def _directory(self, project_id: str) -> Path:
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise StudioError("Choose a saved project or create a storyboard first.")
        return self.root / project_id

    def _save(self, project: dict):
        directory = self._directory(project["id"])
        directory.mkdir(parents=True, exist_ok=True)
        project["updated_at"] = _now()
        project["project_path"] = str(directory / "project.json")
        temporary = directory / "project.tmp"
        temporary.write_text(json.dumps(project, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        replace_file(temporary, directory / "project.json")

    def _read(self, project_id: str) -> dict:
        try:
            path = self._directory(project_id) / "project.json"
            project = json.loads(path.read_text(encoding="utf-8"))
            if project["id"] != project_id:
                raise ValueError
            return project
        except (FileNotFoundError, KeyError, ValueError):
            raise StudioError("This project is missing or unreadable. Create a new storyboard.") from None

    def load_project(self, project_id: str) -> dict:
        with self._lock:
            return self._read(project_id)

    def list_projects(self) -> list[dict]:
        with self._lock:
            projects = []
            for directory in self.root.iterdir():
                if directory.is_dir() and re.fullmatch(r"[a-f0-9]{32}", directory.name):
                    try:
                        projects.append(self._read(directory.name))
                    except (StudioError, OSError):
                        continue
            return sorted(projects, key=lambda p: p.get("updated_at", ""), reverse=True)

    def create_project(self, brief: dict, copy_mode: str = "template", logo_path: str | None = None,
                       screenshot_path: str | None = None, progress=None, *, creative=None, campaign=None,
                        recent_projects=None, source_warnings=None, scene_image_paths=None, demo_path=None) -> dict:
        brief = validate_brief(brief)
        if copy_mode not in ("template", "gemini"):
            raise StudioError("Choose Template copy or Gemini copy.")
        if scene_image_paths is not None and (not isinstance(scene_image_paths, list) or len(scene_image_paths) != 4
                                             or any(not isinstance(p, str) or not p for p in scene_image_paths)):
            raise StudioError("Supply exactly four scene images in storyboard order.")
        _progress(progress, .1, "Validating the product brief")
        directory = self.root / uuid.uuid4().hex
        directory.mkdir()
        assets = {}
        media = {}
        try:
            for label, source in (("logo", logo_path), ("screenshot", screenshot_path)):
                if source:
                    target = directory / f"{label}.png"
                    _normalize_image(source, target)
                    assets[label] = str(target)
            for index, source in enumerate(scene_image_paths or [], 1):
                target = directory / f"scene_{index}.png"
                _normalize_image(source, target)
                assets[f"scene_{index}"] = str(target)
            if demo_path:
                target = directory / "demo.mp4"
                media["demo"] = normalize_video(demo_path, target)
                assets["demo"] = str(target)
            _progress(progress, .25, "Writing with Gemini (uses API credits)" if copy_mode == "gemini" else "Composing a factual template draft — no AI request")
            structure = variant_storyboard(brief, creative) if creative else template_storyboard(brief)
            strategy = deterministic_strategy(brief, creative, [p["scenes"][0]["headline"] for p in (recent_projects or [])[-10:]])
            evidence = {"screen_recording": bool(demo_path), "product_image": bool(screenshot_path),
                        "public_or_uploaded_scene_images": len(scene_image_paths or [])}
            strategy["proof_method"] = "screen_recording" if demo_path else "product_image" if screenshot_path or scene_image_paths else "benefit_card"
            strategy["visual_strategy"] = ("Edit the supplied real recording at its original speed." if demo_path else
                                           "Use only the supplied product pictures, with wide/detail camera cuts." if screenshot_path or scene_image_paths else
                                           "Use kinetic typography from the supplied facts; no product interface is available.")
            if copy_mode == "gemini":
                avoid = [p["scenes"][0]["headline"] for p in (recent_projects or [])[-10:]]
                recent_scripts = [p["scenes"] for p in (recent_projects or [])[-8:]]
                for attempt in range(2):
                    generated = generate_storyboard(brief, structure=structure,
                                                     direction={**(creative or {}), "visual_evidence": evidence}, avoid=avoid,
                                                    recent_scripts=recent_scripts, return_strategy=True)
                    if isinstance(generated, tuple):
                        scenes, strategy = generated
                    else:
                        # Keeps injected/offline provider doubles compatible with the service contract.
                        scenes = generated
                    if not creative:
                        break
                    reason = duplicate_reason(scenes, creative, recent_projects or [])
                    if not reason:
                        break
                    avoid.append(scenes[0]["headline"])
                    if attempt == 1:
                        raise StudioError(f"Gemini returned a repeated creative after one bounded retry: {reason}")
            else:
                scenes = structure
            # Strategy metadata is saved with the project so the chosen creative idea is auditable.
            strategy = {**strategy, "source": "gemini" if copy_mode == "gemini" else "template", "visual_evidence": evidence}
            notices = ["Review every claim before publishing. Only you can confirm product accuracy.", *(source_warnings or [])]
            if copy_mode == "template":
                notices.append("Template copy uses your supplied text. It is not AI-generated or automatically translated.")
            if not screenshot_path and not scene_image_paths and not demo_path:
                notices.append("No product visuals supplied: this is a text-only film. Import public-page captures or upload product images/a real screen recording to show the product.")
            if (screenshot_path or scene_image_paths) and not demo_path:
                notices.append("Product images use editorial camera moves; they do not demonstrate clicks or task completion. Add a real screen recording for a usage demo.")
            if demo_path and media["demo"]["duration"] < brief["duration"] - .5:
                notices.append(f"The real recording is {media['demo']['duration']:g}s; its last frame is held for the remainder of this {brief['duration']}s film. Upload longer footage for continuous action.")
            project = {"schema_version": 1, "id": directory.name, "name": brief["name"], "brief": brief,
                       "scenes": scenes, "assets": assets, "copy_mode": copy_mode, "revision": 1,
                       "created_at": _now(), "updated_at": _now(), "status": "draft", "error": None,
                       "draft_path": None, "final_path": None, "poster_path": None, "warnings": notices,
                       "renders": []}
            project["creative_strategy"] = strategy
            project["media"] = media
            if creative:
                project["creative"] = {**creative, "signature": signature(scenes, creative)}
            if campaign:
                project["campaign"] = campaign
            with self._lock:
                self._save(project)
            _progress(progress, 1, "Storyboard ready. Review and edit all four scenes before rendering.")
            return project
        except Exception:
            # Only this freshly-created UUID directory is removed, never user source assets.
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def parse_ad_prompt(self, prompt: str) -> PromptBrief:
        """Extract a factual brief from a prompt without calling a provider."""
        return parse_ad_prompt(prompt)

    def create_prompt_project(self, prompt: str, copy_mode: str = "template", logo_path: str | None = None,
                              screenshot_path: str | None = None, progress=None, *, scene_image_paths=None,
                              demo_path=None) -> dict:
        """Create a normal editable project from a complete natural-language brief.

        The prompt is parsed before any project directory is created. Incomplete
        prompts therefore cannot consume a project ID or silently produce made-up
        copy.
        """
        parsed = self.parse_ad_prompt(prompt)
        if not parsed.complete:
            raise StudioError(parsed.message)
        return self.create_project(parsed.brief, copy_mode=copy_mode, logo_path=logo_path,
                                   screenshot_path=screenshot_path, progress=progress,
                                   scene_image_paths=scene_image_paths, demo_path=demo_path)

    def update_storyboard(self, project_id: str, rows: list[list]) -> dict:
        if hasattr(rows, "tolist"):
            rows = rows.tolist()
        if not isinstance(rows, list) or any(not isinstance(r, (list, tuple)) or len(r) != 5 for r in rows):
            raise StudioError("The storyboard needs five columns: scene, headline, supporting text, voiceover, seconds.")
        with self._lock:
            project = self._read(project_id)
            if project["status"] == "rendering":
                raise StudioError("Wait for the current render or cancel it before editing this project.")
            scenes = validate_scenes([dict(zip(("kind", "headline", "body", "narration", "duration"), row)) for row in rows],
                                     project["brief"]["duration"])
            if scenes != project["scenes"]:
                project.update(scenes=scenes, revision=project["revision"] + 1, status="draft", error=None,
                               draft_path=None, final_path=None, poster_path=None)
                self._save(project)
            return project

    def cancel(self, project_id: str) -> bool:
        with self._lock:
            event = self._cancels.get(project_id)
            if event:
                event.set()
                return True
            return False

    def render_project(self, project_id: str, quality: str = "draft", narration: bool = False,
                       progress=None, *, include_sfx: bool = False) -> dict:
        if quality not in ("draft", "final"):
            raise StudioError("Choose Draft preview or Final export.")
        if not self._render_lock.acquire(blocking=False):
            raise StudioError("Another video is rendering. Wait for it to finish before starting another export.")
        process_lock = FileLock(self.root / ".render.lock", "Another studio process is rendering. Retry after it finishes.")
        try:
            process_lock.acquire()
        except Exception:
            self._render_lock.release()
            raise
        project = None
        try:
            with self._lock:
                project = self._read(project_id)
                validate_scenes(project["scenes"], project["brief"]["duration"])
                event = self._cancels[project_id] = threading.Event()
                project.update(status="rendering", error=None)
                # Do not let an old artifact masquerade as this attempted export.
                project[f"{quality}_path"] = None
                self._save(project)
            directory = self._directory(project_id) / "renders" / uuid.uuid4().hex
            callback = lambda value, message: _progress(progress, value, message)
            renderer, renderer_version = self._renderer_backend()
            result = renderer(copy.deepcopy(project), directory, quality, bool(narration),
                              self.root / ".audio-cache", callback, event,
                              include_sfx=bool(include_sfx))
            result.setdefault("renderer_version", renderer_version)
            with self._lock:
                if event.is_set():
                    raise RenderCancelled("Render cancelled. No incomplete export was published.")
                project.update(status="ready", error=None, poster_path=result["poster"])
                project[f"{quality}_path"] = result["video"]
                project["renders"].append({"quality": quality, "revision": project["revision"], "narrated": bool(narration),
                                            "sfx": bool(include_sfx),
                                           "created_at": _now(), **result})
                self._save(project)
            _progress(progress, 1, "Verified export ready" if quality == "final" else "Draft ready — lower-resolution preview, not final quality")
            return project
        except Exception as exc:
            if isinstance(exc, StudioError):
                message = str(exc)
            else:
                message = "A local rendering error occurred. Check installed dependencies and retry; your storyboard is saved."
            if project is not None:
                with self._lock:
                    project.update(status="cancelled" if isinstance(exc, RenderCancelled) else "failed", error=message)
                    self._save(project)
            if isinstance(exc, StudioError):
                raise
            raise StudioError(message) from None
        finally:
            with self._lock:
                self._cancels.pop(project_id, None)
            process_lock.release()
            self._render_lock.release()

    def import_product(self, url: str, refresh: bool = False, progress=None, *, capture_visuals: bool = False, record_tour: bool = False) -> dict:
        return self.catalog.import_website(url, refresh=refresh, progress=progress, capture_visuals=capture_visuals, record_tour=record_tour)

    def suggest_brief_fields(self, name: str, description: str, audience: str, language: str = "English",
                             existing_problem: str = "", existing_benefits: str = "") -> dict:
        """Generate reviewable brief suggestions through Groq, never Gemini."""
        return suggest_brief_fields(name, description, audience, language, existing_problem, existing_benefits)

    def save_product(self, product_id: str | None, brief: dict, logo_path=None, screenshot_path=None, scene_image_paths=None, demo_path=None) -> dict:
        return self.catalog.save(product_id, brief, logo_path, screenshot_path, scene_image_paths, demo_path)

    def load_product(self, product_id: str) -> dict:
        return self.catalog.load(product_id)

    def list_products(self) -> list[dict]:
        return self.catalog.list()

    def list_product_ads(self, product_id: str) -> list[dict]:
        self.catalog.load(product_id)
        return sorted([p for p in self.list_projects() if p.get("campaign", {}).get("product_id") == product_id],
                      key=lambda p: p["campaign"].get("ordinal", 0))

    def create_daily_project(self, product_id: str, *, campaign_date: str | None = None, goal: str = "",
                             copy_mode: str = "template", new_take: bool = False, progress=None) -> dict:
        goal = text(goal, "Campaign goal", 300, False)
        try:
            day = date.fromisoformat(campaign_date.strip()).isoformat() if campaign_date and campaign_date.strip() else datetime.now(timezone.utc).date().isoformat()
        except (ValueError, AttributeError):
            raise StudioError("Use a campaign date in YYYY-MM-DD format, or leave it blank for today (UTC).") from None
        with self._campaign_lock, FileLock(self.root / ".campaign.lock", "Another daily storyboard is being prepared. Wait and retry; no duplicate job was submitted."):
            product = self.catalog.load(product_id)
            if not product.get("approved"):
                raise StudioError("Review the imported product facts once, then click Save product profile before creating daily ads.")
            history = self.list_product_ads(product_id)
            matching = [p for p in history if p["campaign"]["date"] == day]
            if matching and not new_take:
                project = matching[-1]
                project["reused_daily"] = True
                _progress(progress, 1, f"Reusing the saved ad for {day}; no new copy request")
                return project
            plan = select_plan(product["brief"], history, goal)
            brief = rotated_brief(product["brief"], plan)
            notices = ["Daily variation uses your saved product facts. New angles do not prove advertising performance."]
            discovery = product.get("discovery") or {}
            notices.extend(discovery.get("warnings", []))
            discovered_at = discovery.get("discovered_at")
            if discovered_at:
                try:
                    if (datetime.now(timezone.utc) - datetime.fromisoformat(discovered_at.replace("Z", "+00:00"))).days >= 30:
                        notices.append("Website evidence is over 30 days old. Recheck it if features, pricing, or positioning have changed.")
                except (TypeError, ValueError):
                    pass
            campaign = {"product_id": product_id, "product_revision": product["revision"], "date": day,
                        "take": len(matching) + 1, "ordinal": len(history) + 1, "goal": goal,
                        "source_url": product.get("source_url", "")}
            return self.create_project(brief, copy_mode=copy_mode,
                                        logo_path=product.get("assets", {}).get("logo"),
                                        screenshot_path=product.get("assets", {}).get("screenshot"), progress=progress,
                                        creative=plan, campaign=campaign, recent_projects=history, source_warnings=notices,
                                         scene_image_paths=([product["assets"][f"scene_{i}"] for i in range(1, 5)]
                                                            if all(product.get("assets", {}).get(f"scene_{i}") for i in range(1, 5)) else None),
                                         demo_path=product.get("assets", {}).get("demo"))

    def complete_daily_ad(self, project_id: str, *, quality: str = "final", narration: bool = False,
                          include_sfx: bool = False, progress=None) -> dict:
        project = self.load_project(project_id)
        if quality not in ("draft", "final"):
            raise StudioError("Choose Draft preview or Final export.")
        path = project.get(f"{quality}_path")
        renderer_version = self._renderer_version()
        compatible = any(r["quality"] == quality and r.get("revision") == project["revision"]
                           and r.get("narrated") == bool(narration)
                            and r.get("sfx", False) == bool(include_sfx)
                            and r.get("renderer_version") == renderer_version
                           and r.get("video") == path
                          and (not narration or r.get("narration_settings") == narration_settings())
                          for r in project.get("renders", []))
        if project["status"] == "ready" and path and Path(path).is_file() and compatible:
            width, height = ASPECTS[project["brief"]["aspect"]]
            if quality == "draft":
                width, height = width // 3, height // 3
            try:
                check_export(Path(path), width, height, 24 if quality == "draft" else 30,
                               project["brief"]["duration"], bool(narration or include_sfx))
            except StudioError:
                pass  # A missing/corrupted export is rebuilt from the same saved storyboard.
            else:
                _progress(progress, 1, "Existing verified daily export reused — no new render or narration request")
                return project
        return self.render_project(project_id, quality=quality, narration=narration,
                                   include_sfx=include_sfx, progress=progress)

    def generate_daily_ad(self, product_id: str, *, campaign_date=None, goal="", copy_mode="template", new_take=False,
                          quality="final", narration=False, include_sfx=False, progress=None) -> dict:
        if quality not in ("draft", "final"):
            raise StudioError("Choose Draft preview or Final export.")
        project = self.create_daily_project(product_id, campaign_date=campaign_date, goal=goal, copy_mode=copy_mode,
                                            new_take=new_take, progress=progress)
        return self.complete_daily_ad(project["id"], quality=quality, narration=narration,
                                      include_sfx=include_sfx, progress=progress)
