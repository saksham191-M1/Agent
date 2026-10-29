"""Reusable, source-backed product profiles. Discovery is a candidate, never approval."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .assets import normalize_image, normalize_video
from .locking import replace_file
from .models import StudioError, validate_brief

DEFAULTS = {"name": "", "description": "", "audience": "", "problem": "", "benefits": [],
            "cta": "Explore the product", "url": "", "color": "#a78bfa", "template": "spotlight",
            "aspect": "9:16", "duration": 20, "tone": "Confident", "language": "English"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def source_key(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StudioError("Enter the product's public website URL.")
    value = value.strip()
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError
        if parsed.port not in (None, 443) or len(value) > 2048:
            raise ValueError
        # Query strings can contain session/tracking data and are unnecessary for this importer.
        return urlunsplit(("https", parsed.hostname.lower(), parsed.path.rstrip("/") or "/", "", ""))
    except ValueError:
        raise StudioError("Use a public HTTPS website address without credentials or a custom port.") from None


class ProductCatalog:
    def __init__(self, root: Path):
        self.root = root / "products"
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def directory(self, product_id: str) -> Path:
        if not isinstance(product_id, str) or not re.fullmatch(r"[a-f0-9]{32}", product_id):
            raise StudioError("Choose a saved product profile first.")
        return self.root / product_id

    def _write(self, product: dict):
        directory = self.directory(product["id"])
        directory.mkdir(parents=True, exist_ok=True)
        product["updated_at"] = now()
        product["profile_path"] = str(directory / "profile.json")
        temporary = directory / "profile.tmp"
        temporary.write_text(json.dumps(product, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        replace_file(temporary, directory / "profile.json")

    def load(self, product_id: str) -> dict:
        with self.lock:
            try:
                product = json.loads((self.directory(product_id) / "profile.json").read_text(encoding="utf-8"))
                if product["id"] != product_id:
                    raise ValueError
                return product
            except (OSError, KeyError, ValueError):
                raise StudioError("This product profile is missing or unreadable.") from None

    def list(self) -> list[dict]:
        with self.lock:
            products = []
            for directory in self.root.iterdir():
                if re.fullmatch(r"[a-f0-9]{32}", directory.name) and directory.is_dir():
                    try:
                        products.append(self.load(directory.name))
                    except StudioError:
                        continue
            return sorted(products, key=lambda p: p.get("updated_at", ""), reverse=True)

    def _new(self, url: str = "") -> dict:
        return {"schema_version": 1, "id": uuid.uuid4().hex, "name": "New product", "source_url": url,
                "brief": copy.deepcopy(DEFAULTS), "assets": {}, "discovery": {}, "approved": False,
                "revision": 0, "created_at": now(), "updated_at": now(), "approved_at": None}

    def import_website(self, url: str, *, refresh: bool = False, progress=None, capture_visuals: bool = False,
                       record_tour: bool = False) -> dict:
        from .discovery import discover_site
        key = source_key(url)
        with self.lock:
            existing = next((p for p in self.list() if p.get("source_url") == key), None)
            if existing and existing.get("discovery") and not refresh:
                if (capture_visuals and not existing["discovery"].get("captures")
                        or record_tour and not existing["discovery"].get("captures", {}).get("tour")):
                    existing["refresh_notice"] = "This cached profile is missing the requested page captures/walkthrough. Turn Recheck the website on to capture current product visuals, or upload a real recording."
                if progress:
                    progress(1, "Using the cached product profile — no website request made")
                return existing
            product = existing or self._new(key)
            directory = self.directory(product["id"])
            destination = directory / "discoveries" / uuid.uuid4().hex
            destination.mkdir(parents=True, exist_ok=True)
            try:
                options = {"capture_visuals": True} if capture_visuals else {}
                if record_tour:
                    options["record_tour"] = True
                discovery = discover_site(key, destination, progress=progress, **options)
                partial = {k: v for k, v in discovery.get("brief", {}).items() if k in DEFAULTS and v}
                if existing and existing.get("approved"):
                    # Never overwrite human-reviewed facts or branding during a website refresh.
                    product["pending_discovery"] = discovery
                    product["refresh_notice"] = "New website evidence is saved. Reviewed facts and saved assets are unchanged. New page captures are staged in the form; review them and Save product profile to adopt them."
                else:
                    product["brief"].update(partial)
                    product["brief"]["url"] = product["brief"].get("url") or discovery.get("url", key)
                    product["assets"] = discovery.get("assets", {})
                    product["discovery"] = discovery
                    product["name"] = product["brief"].get("name") or key
                self._write(product)
                return product
            except Exception:
                shutil.rmtree(destination, ignore_errors=True)
                raise

    def save(self, product_id: str | None, brief: dict, logo_path=None, screenshot_path=None, scene_image_paths=None, demo_path=None) -> dict:
        brief = validate_brief(brief)
        if scene_image_paths is not None and (not isinstance(scene_image_paths, list) or len(scene_image_paths) != 4
                                             or any(not isinstance(p, str) or not p for p in scene_image_paths)):
            raise StudioError("Supply exactly four scene images in storyboard order.")
        with self.lock:
            product = self.load(product_id) if product_id else self._new()
            directory = self.directory(product["id"])
            asset_dir = directory / "assets" / uuid.uuid4().hex
            asset_dir.mkdir(parents=True, exist_ok=True)
            assets = dict(product.get("assets", {}))
            try:
                sources = [("logo", logo_path), ("screenshot", screenshot_path)]
                sources.extend((f"scene_{i}", path) for i, path in enumerate(scene_image_paths or [], 1))
                for kind, source in sources:
                    if source:
                        target = asset_dir / f"{kind}.png"
                        normalize_image(str(source), target)
                        assets[kind] = str(target)
                if demo_path:
                    target = asset_dir / "demo.mp4"
                    normalize_video(str(demo_path), target)
                    assets["demo"] = str(target)
                # Content fingerprints avoid version bumps solely from a copied filename.
                if any(not Path(path).is_file() for path in assets.values()):
                    raise StudioError("A saved brand image is missing. Re-upload it before saving this profile.")
                image_hashes = {kind: hashlib.sha256(Path(path).read_bytes()).hexdigest() for kind, path in assets.items()}
                fingerprint = hashlib.sha256(json.dumps({"brief": brief, "images": image_hashes}, sort_keys=True).encode()).hexdigest()
                changed = product.get("fingerprint") != fingerprint
                product.update(name=brief["name"], brief=brief, assets=assets, fingerprint=fingerprint, approved=True,
                               approved_at=now(), revision=product["revision"] + int(changed))
                product["revision"] = max(1, product["revision"])
                product.pop("refresh_notice", None)
                self._write(product)
                return product
            except Exception:
                shutil.rmtree(asset_dir, ignore_errors=True)
                raise
