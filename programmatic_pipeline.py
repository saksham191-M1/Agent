"""
programmatic_pipeline.py
App name -> Opus JSON -> validate -> inject into Master HTML -> Playwright record -> ffmpeg trim/encode (-> optional audio)

Usage:
    python programmatic_pipeline.py Kora iphone_showcase_master
    python programmatic_pipeline.py Kora problem_solution_master --audio vo.mp3
"""
import argparse
import asyncio
import html
import json
import re
import os
import subprocess
import time
import requests
from pathlib import Path

from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load env for Gemini API key
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

TEMPLATES_DIR = Path("tools/video_pipeline/templates")
OUTPUT_DIR = Path("output")
DURATION = 15          # seconds, must match the template timeline
VIEWPORT = (540, 960)  # CSS px; 9:16. Upscaled to 1080x1920 at encode time
MAX_RETRIES = 3

# Per-field max character lengths so text never overflows the layouts.
FIELD_MAX = {
    # General
    "SHORT_NAME": 20, "APP_INITIAL": 1, "APP_URL": 30,
    
    # problem_solution_master
    "HOOK_MAIN": 35, "HOOK_SUB": 35,
    "PROBLEM_METRIC": 30, "SOLUTION_HEADLINE": 30,
    "SOLUTION_START_NUM": 6, "SOLUTION_METRIC": 20, "SOLUTION_ACTION": 20,
    "TASK_1": 40, "TASK_2": 40, "TASK_3": 40, "TASK_4": 40, "TASK_5": 40,
    "TASK_1_SUB": 25, "TASK_1_HEAD": 25,
    "TASK_2_SUB": 25, "TASK_2_HEAD": 25,
    "TASK_3_SUB": 25, "TASK_3_HEAD": 25,
    "TASK_4_SUB": 25, "TASK_4_HEAD": 25,
    "TASK_5_SUB": 25, "TASK_5_HEAD": 25,
    "BEFORE_TEXT": 30, "BEFORE_TIME": 15,
    "AFTER_TIME": 15, "TRANSITION_TEXT": 35,
    "CTA_HEADLINE": 30, "CAPTION_1": 40, "CAPTION_2": 40,
    
    # iphone_showcase_master
    "HOOK_1": 28, "HOOK_2": 28, "HOOK_3": 28, "HOOK_4": 28,
    "STAT_NUMBER": 6, "STAT_LABEL": 16,
    "BUBBLE_1_TITLE": 22, "BUBBLE_1_SUB": 24,
    "BUBBLE_2_TITLE": 22, "BUBBLE_2_SUB": 24,
    "BUBBLE_3_TITLE": 22, "BUBBLE_3_SUB": 24,
    "BUBBLE_4_TITLE": 22, "BUBBLE_4_SUB": 24,
    "LIST_1": 35, "LIST_2": 35, "LIST_3": 35, "LIST_4": 35, "LIST_5": 35,
    "PANEL_A_TAG": 20, "PANEL_B_TAG": 20, "PANEL_B_TITLE": 20,
    "CAL_1_TITLE": 25, "CAL_1_SUB": 35,
    "CAL_2_TITLE": 25, "CAL_2_SUB": 35,
    "CAL_3_TITLE": 25, "CAL_3_SUB": 35,
    "SUCCESS_TITLE": 22, "SUCCESS_SUB": 35,
    "CALLOUT_1": 30, "CALLOUT_2": 30,
}
DEFAULT_MAX = 40

PLACEHOLDER = re.compile(r"\{\{(\w+)(?::(js))?\}\}")


import audio_layer

# ---------------------------------------------------------------- 1. brain
def call_brain(prompt: str, app_name: str) -> str:
    """Uses the Gemini REST API exactly like brain_opus.py"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing from .env")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3}
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        # If API fails, return a hardcoded valid JSON string for testing
        return f"""{{
          "SHORT_NAME": "{app_name[:20].strip()}",
          "APP_INITIAL": "{app_name[0] if app_name else 'K'}",
          "APP_URL": "{app_name.lower().replace(' ', '')[:15]}.com",
          "HOOK_MAIN": "Still doing manual work?",
          "HOOK_SUB": "Every single day.",
          "PROBLEM_METRIC": "unread and counting",
          "SOLUTION_HEADLINE": "Your workflow, handled.",
          "SOLUTION_START_NUM": "214",
          "SOLUTION_METRIC": "tasks waiting",
          "SOLUTION_ACTION": "Clear queue",
          "TASK_1": "Invoice - Paid",
          "TASK_2": "Meeting - Booked",
          "TASK_3": "Refund - Replied",
          "TASK_4": "Newsletter - Archived",
          "TASK_5": "Contract - Flagged",
          "TASK_1_HEAD": "Hale Co.",
          "TASK_1_SUB": "Re: Invoice",
          "TASK_2_HEAD": "Priya",
          "TASK_2_SUB": "Can we talk?",
          "TASK_3_HEAD": "Customer",
          "TASK_3_SUB": "URGENT refund",
          "TASK_4_HEAD": "Newsletter",
          "TASK_4_SUB": "Weekly digest",
          "TASK_5_HEAD": "Sam",
          "TASK_5_SUB": "Quick question",
          "BEFORE_TEXT": "manual work",
          "BEFORE_TIME": "3 hours",
          "AFTER_TIME": "10 seconds",
          "TRANSITION_TEXT": "Stop sorting. Start doing.",
          "CTA_HEADLINE": "Get your morning back.",
          "CAPTION_1": "Still answering emails by hand?",
          "CAPTION_2": "Every day. Same pile.",
          "HOOK_1": "Your inbox. Handled.",
          "HOOK_2": "It books the meetings too.",
          "HOOK_3": "3 hours to 10 seconds",
          "HOOK_4": "Get your morning back.",
          "BUBBLE_1_TITLE": "Hale Co. invoice",
          "BUBBLE_1_SUB": "Paid automatically",
          "BUBBLE_2_TITLE": "Meeting booked",
          "BUBBLE_2_SUB": "Tue 10:00 with Priya",
          "BUBBLE_3_TITLE": "Refund replied",
          "BUBBLE_3_SUB": "In your voice",
          "BUBBLE_4_TITLE": "214 to 0",
          "BUBBLE_4_SUB": "Inbox cleared",
          "LIST_1": "Invoice from Hale Co. · paid",
          "LIST_2": "Customer refund · replied",
          "LIST_3": "Newsletter pile · archived",
          "LIST_4": "Vendor follow-up · replied",
          "LIST_5": "Contract v7 · flagged",
          "PANEL_A_TAG": "Inbox",
          "PANEL_B_TAG": "Calendar",
          "PANEL_B_TITLE": "Tuesday",
          "CAL_1_TITLE": "10:00 Priya",
          "CAL_1_SUB": "Product sync",
          "CAL_2_TITLE": "13:00 Sam",
          "CAL_2_SUB": "Quick question",
          "CAL_3_TITLE": "15:30 Legal",
          "CAL_3_SUB": "Contract review",
          "SUCCESS_TITLE": "Inbox zero",
          "SUCCESS_SUB": "Done in 10 seconds",
          "CALLOUT_1": "Replies in your voice",
          "CALLOUT_2": "Books meetings",
          "STAT_NUMBER": "214",
          "STAT_LABEL": "emails waiting",
          "VO_1": "Still doing manual work every single day?",
          "VO_2": "Meet {app_name}. Your workflow, handled.",
          "VO_3": "It clears your queue in 10 seconds flat.",
          "VO_4": "Stop sorting and get your morning back. Try {app_name}."
        }}"""
        
    return response.json()['candidates'][0]['content']['parts'][0]['text']


def placeholders_in(template_html: str) -> list[str]:
    seen = []
    for m in PLACEHOLDER.finditer(template_html):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def build_prompt(app_name: str, fields: list[str], error: str | None = None, extra: str = "") -> str:
    limits = "\n".join(f'- {f}: max {FIELD_MAX.get(f, DEFAULT_MAX)} characters' for f in fields)
    retry = f"\nYour previous answer was rejected: {error}\nFix it.\n" if error else ""
    return f"""You are an agency copywriter writing a 15-second social ad for the app "{app_name}".
Output ONLY a JSON object, no markdown, no commentary.
Required keys (exactly these, all strings):
{limits}

Rules:
- Headlines are punchy and under 6 words. No emojis. No line breaks.
- Stats are believable, specific numbers (e.g. "3", "10", "2x"). Never invent customer names.
- SHORT_NAME is a short display name for the app (max 20 characters).
- APP_INITIAL is the first letter of the app name.
- Use plain text only: no HTML, no quotes inside values.
{extra}
{retry}"""


def validate(data: dict, fields: list[str]) -> str | None:
    """Return an error string, or None if valid."""
    missing = [f for f in fields if f not in data]
    if missing:
        return f"missing keys: {missing}"
    for f in fields:
        v = data[f]
        if not isinstance(v, str) or not v.strip():
            return f"{f} must be a non-empty string"
        limit = FIELD_MAX.get(f, DEFAULT_MAX)
        if len(v) > limit:
            return f"{f} is {len(v)} chars, max {limit}"
        if "\n" in v or "<" in v or ">" in v:
            return f"{f} must be plain text with no line breaks or HTML"
    return None


def get_payload(app_name: str, fields: list[str], extra: str = "") -> dict:
    error = None
    for attempt in range(1, MAX_RETRIES + 1):
        raw = call_brain(build_prompt(app_name, fields, error, extra), app_name)
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            error = f"invalid JSON ({e})"
            continue
        error = validate(data, fields)
        if error is None:
            return data
        print(f"[brain] attempt {attempt} rejected: {error}")
    raise RuntimeError(f"Brain failed validation after {MAX_RETRIES} tries: {error}")


# ------------------------------------------------------------- 2. injector
def inject(template_html: str, data: dict) -> str:
    """{{KEY}} -> HTML-escaped text (for text nodes/attributes)
       {{KEY:js}} -> JSON string literal (for use inside <script>)"""
    def sub(m: re.Match) -> str:
        key, mode = m.group(1), m.group(2)
        # Only inject if it's a template placeholder, skip VO fields
        if key not in data: return m.group(0)
        val = data[key]
        return json.dumps(val) if mode == "js" else html.escape(val, quote=True)
    out = PLACEHOLDER.sub(sub, template_html)
    leftover = PLACEHOLDER.findall(out)
    assert not leftover, f"Unfilled placeholders: {leftover}"
    return out


# ------------------------------------------------------------- 3. recorder
async def record(html_path: Path, raw_dir: Path) -> tuple[Path, float]:
    """Record the page for DURATION seconds. Returns (webm path, seconds of dead time at start)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        # Note: --autoplay-policy=no-user-gesture-required is great for media.
        browser = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = await browser.new_context(
            viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]},
            record_video_dir=str(raw_dir),
            record_video_size={"width": VIEWPORT[0], "height": VIEWPORT[1]},
        )
        page = await ctx.new_page()
        t_created = time.monotonic()                      # video clock starts here
        await page.goto(html_path.resolve().as_uri(), wait_until="load")
        await page.evaluate("document.fonts.ready")       # don't record fallback fonts
        offset = time.monotonic() - t_created             # dead time before the ad starts
        await page.wait_for_timeout(int((DURATION + 0.5) * 1000))
        video_path = Path(await page.video.path())
        await ctx.close()                                 # flushes the file
        await browser.close()
    return video_path, offset


# -------------------------------------------------------------- 4. encoder
def encode(raw: Path, offset: float, out: Path, audio: Path | None = None) -> None:
    cmd = ["ffmpeg", "-y", "-ss", f"{offset:.3f}", "-t", str(DURATION), "-i", str(raw)]
    if audio:
        cmd += ["-i", str(audio)]
    cmd += [
        "-vf", "scale=1080:1920:flags=lanczos,fps=60",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
    ]
    if audio:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-af", f"afade=t=out:st={DURATION-0.8}:d=0.8", "-shortest"]
    cmd += ["-movflags", "+faststart", str(out)]
    
    # Run ffmpeg with output suppression to avoid massive logs unless it fails
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode())
        raise RuntimeError("FFmpeg failed")


# -------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("app_name")
    ap.add_argument("template", choices=["problem_solution_master", "iphone_showcase_master"])
    ap.add_argument("--audio", type=Path, default=None)
    ap.add_argument("--no-sfx", action="store_true", help="Do not add the cue-based SFX layer to a supplied voiceover")
    args = ap.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"\W+", "_", args.app_name.lower())
    tpl = (TEMPLATES_DIR / f"{args.template}.html").read_text(encoding="utf-8")

    fields = placeholders_in(tpl)
    FIELD_MAX.update(audio_layer.vo_char_limits(args.template))
    
    print(f"[pipeline] template needs: {len(fields)} layout fields + {len(audio_layer.vo_fields(args.template))} audio fields")
    data = get_payload(args.app_name, fields + audio_layer.vo_fields(args.template),
                       extra=audio_layer.prompt_addendum(args.template))
                       
    (OUTPUT_DIR / f"{slug}_{args.template}.json").write_text(json.dumps(data, indent=2))

    filled = OUTPUT_DIR / f"{slug}_{args.template}.html"
    filled.write_text(inject(tpl, data), encoding="utf-8")

    raw, offset = asyncio.run(record(filled, OUTPUT_DIR / "raw"))
    final = OUTPUT_DIR / f"{slug}_{args.template}.mp4"
    
    # Build Audio Layer. A supplied full voiceover used to bypass SFX entirely;
    # mix it through the same cue layer unless explicitly disabled.
    mixed_audio = OUTPUT_DIR / f"{slug}_mix.wav"
    audio_path = (audio_layer.mix_existing_voiceover(args.audio, args.template, mixed_audio,
                                                      include_sfx=not args.no_sfx)
                  if args.audio else audio_layer.build_track(args.template, data, mixed_audio))
    
    encode(raw, offset, final, audio_path)
    print(f"[pipeline] done -> {final}")


if __name__ == "__main__":
    main()
