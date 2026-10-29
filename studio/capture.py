"""Capture static public marketing sections through the existing bounded importer.

Chromium renders the fetched HTML/CSS/images locally. Site JavaScript, third-party
resources, forms, and authenticated application routes are never executed/fetched.
"""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .discovery import _Fetcher, _normalize_url, _origin, _parse_page
from .models import StudioError
from .assets import normalize_video

_STATIC_STYLE = b"<style>.reveal,[data-aos]{opacity:1!important;transform:none!important;visibility:visible!important} *{animation:none!important;transition:none!important} html{scroll-behavior:auto!important}</style>"


@contextmanager
def _public_page(url, width, *, fetcher=None, homepage=None, recording_dir=None):
    """Reuse the importer's fetched evidence and budget for actual page layout."""
    start = _normalize_url(url)
    fetcher = fetcher or _Fetcher()
    homepage = homepage or fetcher.fetch(start, "html", _origin(start))
    _parse_page(homepage)  # Reject login/blocking screens just as the importer does.
    origin = _origin(homepage.url)
    cached = {homepage.url: homepage}
    notices = ["Actual public-page captures, with source URLs. Site scripts and external fonts are disabled; these are website visuals, not a recorded app task."]
    from playwright.sync_api import sync_playwright

    def resource(route):
        try:
            address = _normalize_url(route.request.url)
            kind = {"document": "html", "stylesheet": "css", "image": "image"}.get(route.request.resource_type)
            if (not kind or _origin(address) != origin or route.request.method != "GET"
                    or kind == "html" and address != homepage.url):
                route.abort()
                return
            if address not in cached:
                cached[address] = fetcher.fetch(address, kind, origin)
            response = cached[address]
            # add_style_tag waits for an onload handler that never runs with page JS disabled.
            # Insert our reveal/reset CSS into the static document instead.
            body = response.body + _STATIC_STYLE if kind == "html" else response.body
            route.fulfill(status=200, body=body,
                          content_type=response.headers.get("content-type", "application/octet-stream"))
        except StudioError as exc:
            message = f"An optional page resource was omitted: {exc}"
            if message not in notices:
                notices.append(message)
            route.abort()

    with sync_playwright() as pw:
        context = None
        try:
            browser = pw.chromium.launch(headless=True)
        except Exception:
            raise StudioError("Chromium is unavailable. Run: python -m playwright install chromium") from None
        try:
            video_options = {"record_video_dir": str(recording_dir), "record_video_size": {"width": width, "height": 900}} if recording_dir else {}
            context = browser.new_context(viewport={"width": width, "height": 900},
                                           java_script_enabled=False, service_workers="block",
                                           reduced_motion="reduce", device_scale_factor=1, **video_options)
            context.route("**/*", resource)
            page = context.new_page()
            page._studio_recording_started = time.monotonic()
            page.set_default_timeout(15000)
            page.goto(homepage.url, wait_until="load", timeout=45000)
            # Lazily loaded first-party pictures can be displayed without running
            # site code; we only adjust their documented loading attributes.
            page.evaluate("""() => { for (const img of document.images) {
                img.loading='eager'; if (!img.getAttribute('src') && img.dataset.src) img.src=img.dataset.src;
            }}""")
            page.evaluate("""() => Promise.all([...document.images].map(img =>
                img.complete ? null : new Promise(resolve => {
                    img.addEventListener('load', resolve, {once:true});
                    img.addEventListener('error', resolve, {once:true}); setTimeout(resolve, 3000);
                })))""")
            yield page, homepage.url, notices
        except StudioError:
            raise
        except Exception:
            raise StudioError("The public page could not be captured reliably. Upload a product screenshot or recording.") from None
        finally:
            if context:
                context.close()
            browser.close()


def _manifest(destination, address, width, captures, notices):
    result = {"url": address, "captured_at": datetime.now(timezone.utc).isoformat(),
              "width": width, "captures": captures, "warnings": notices}
    (destination / "sources.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def capture_public_sections(url: str, destination: Path, selectors: list[str], *, width: int = 1200, progress=None) -> dict:
    if not isinstance(selectors, list) or not 1 <= len(selectors) <= 4 or any(
            not isinstance(s, str) or not s.strip() or len(s) > 200 for s in selectors):
        raise StudioError("Choose one to four public-page CSS selectors to capture.")
    if not isinstance(width, int) or not 720 <= width <= 1600:
        raise StudioError("Public capture width must be between 720 and 1600 pixels.")
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with _public_page(url, width) as (page, address, notices):
        captures = []
        for index, selector in enumerate(selectors, 1):
            if progress:
                progress(.4 + .5 * (index - 1) / len(selectors), f"Capturing section {index}/{len(selectors)}: {selector}")
            target = page.locator(selector).first
            if not target.count():
                raise StudioError(f"Public page section was not found: {selector}")
            bounds = target.bounding_box()
            if not bounds or bounds["height"] <= 0 or bounds["width"] * bounds["height"] > 8_000_000:
                raise StudioError("A public page section is empty or too large to capture.")
            path = destination / f"scene-{index}.png"
            target.screenshot(path=str(path), animations="disabled")
            captures.append({"source": address, "selector": selector, "path": str(path)})
        result = _manifest(destination, address, width, captures, notices)
    if progress:
        progress(1, "Public scene images and source manifest saved")
    return result


def capture_public_visuals(url: str, destination: Path, *, fetcher=None, homepage=None, progress=None, record_tour=False) -> dict:
    """Automatic four-shot public website coverage; no invented app interaction."""
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    width = 1200
    if progress:
        progress(.05, "Opening the actual public product page")
    with _public_page(url, width, fetcher=fetcher, homepage=homepage,
                      recording_dir=destination if record_tour else None) as (page, address, notices):
        visible = page.evaluate("""() => ({
            text:document.body.innerText.trim().length,
            images:[...document.images].some(i=>i.naturalWidth>100 && i.naturalHeight>100)
        })""")
        if visible["text"] < 40 and not visible["images"]:
            raise StudioError("The public page has no usable static product content. Supply real screenshots/a recording for this site.")
        positions = page.evaluate("""() => {
            const height=document.documentElement.scrollHeight, max=Math.max(0,height-innerHeight);
            const sections=[...document.querySelectorAll('main section,main>article,main>div,body>section')]
              .map(el=>el.getBoundingClientRect()).filter(r=>r.height>=180 && r.top>=300);
            const positions=[0];
            for(const section of sections) {
                const y=Math.max(0,Math.min(max,section.top-40));
                if(positions.every(p=>Math.abs(p-y)>300)) positions.push(y);
                if(positions.length===4) break;
            }
            if(positions.length<4) return [0,max*.28,max*.62,max];
            return positions;
        }""")
        captures = []
        for index, position in enumerate(positions, 1):
            if progress:
                progress(.3 + .15 * index, f"Capturing product-page shot {index}/4")
            page.evaluate("y=>window.scrollTo(0,y)", position)
            path = destination / f"scene-{index}.png"
            page.screenshot(path=str(path), animations="disabled")
            captures.append({"source": address, "path": str(path), "scroll_y": round(position),
                             "method": "static public-page viewport", "viewport": [width, 900]})
        video_path, recording_offset = None, 0
        actions = []
        if record_tour:
            page.evaluate("window.scrollTo(0,0)")
            page.wait_for_timeout(100)
            recording_offset = max(0, time.monotonic() - page._studio_recording_started)
            # Resolve the path while Playwright is still alive; the file itself
            # is finalized when the context/browser closes below.
            video_path = page.video.path()
            clock = time.monotonic()
            previous = 0
            # Record the real document scrolling through its captured sections.
            # Actual page pixels are used; no task result/interface is generated.
            for index, target in enumerate(positions[1:], 1):
                if progress:
                    progress(.91 + .02 * index, f"Recording the real product-page walkthrough {index}/3")
                target_time = index * 7
                steps = 100
                for step in range(1, steps + 1):
                    p = step / steps
                    eased = p * p * (3 - 2 * p)
                    page.evaluate("y=>window.scrollTo(0,y)", previous + (target - previous) * eased)
                    deadline = (index - 1) * 7 + 7 * p
                    wait = deadline - (time.monotonic() - clock)
                    if wait > 0:
                        page.wait_for_timeout(wait * 1000)
                actions.append({"type": "scroll", "start": (index - 1) * 7, "end": target_time,
                                "from_y": round(previous), "to_y": round(target)})
                previous = target
            wait = 24 - (time.monotonic() - clock)
            if wait > 0:
                page.wait_for_timeout(wait * 1000)
    result = {"url": address, "captured_at": datetime.now(timezone.utc).isoformat(),
              "width": width, "captures": captures, "warnings": notices}
    if video_path:
        try:
            target = destination / "public-page-tour.mp4"
            normalize_video(video_path, target, start_seconds=recording_offset)
            result["tour"] = {"path": str(target), "source": address, "method": "recorded public-page scrolling",
                              "actions": actions, "duration": 24, "authenticated_task": False}
            notices.append("The recorded walkthrough shows the actual public website scrolling. Upload your own recording to demonstrate app clicks or logged-in tasks.")
        except StudioError as exc:
            notices.append(f"The page walkthrough could not be prepared: {exc} The four captured images are still available.")
    (destination / "sources.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    if progress:
        progress(1, "Real product visuals and source manifest saved")
    return result
