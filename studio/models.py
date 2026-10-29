"""Validated product briefs and the single timeline used by video and audio."""
from __future__ import annotations

import math
import re
from urllib.parse import urlparse


class StudioError(Exception):
    """An actionable message safe to display to the user."""


KINDS = ("Hook", "Benefit", "Product", "Call to action")
ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
TEMPLATES = ("spotlight", "problem_solution")


def text(value, label: str, maximum: int, required: bool = True) -> str:
    if not isinstance(value, str):
        raise StudioError(f"{label} must be text.")
    value = " ".join(value.split()).strip()
    if required and not value:
        raise StudioError(f"Add {label.lower()} before continuing.")
    if len(value) > maximum:
        raise StudioError(f"{label} must be at most {maximum} characters (currently {len(value)}).")
    return value


def validate_brief(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise StudioError("The product brief must be an object.")
    result = {
        "name": text(raw.get("name", ""), "Product name", 40),
        "description": text(raw.get("description", ""), "Product description", 800),
        "audience": text(raw.get("audience", ""), "Target audience", 100),
        "problem": text(raw.get("problem", ""), "Customer problem", 180, False),
        "cta": text(raw.get("cta", "Explore the product"), "Call to action", 40),
        "url": text(raw.get("url", ""), "Website", 120, False),
        "color": text(raw.get("color", "#a78bfa"), "Brand color", 7),
        "template": raw.get("template", "spotlight"),
        "aspect": raw.get("aspect", "9:16"),
        "tone": raw.get("tone", "Confident"),
        "language": raw.get("language", "English"),
    }
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", result["color"]):
        raise StudioError("Choose a six-digit brand color, such as #a78bfa.")
    options = {"template": TEMPLATES, "aspect": tuple(ASPECTS),
               "tone": ("Confident", "Friendly", "Bold"), "language": ("English", "Hindi", "Hinglish")}
    for key, choices in options.items():
        if result[key] not in choices:
            raise StudioError(f"Choose a supported {key}: {', '.join(choices)}.")
    if result["template"] == "problem_solution" and not result["problem"]:
        raise StudioError("Describe the real customer problem for the Problem → solution direction.")
    duration = raw.get("duration", 15)
    if isinstance(duration, bool) or not isinstance(duration, (float, int)) or duration not in (15, 20, 30):
        raise StudioError("Choose a video duration of 15, 20, or 30 seconds.")
    result["duration"] = int(duration)
    benefits = raw.get("benefits", "")
    if isinstance(benefits, str):
        benefits = [line.strip(" -•\t") for line in benefits.splitlines() if line.strip()]
    if not isinstance(benefits, list) or not 1 <= len(benefits) <= 6:
        raise StudioError("Add one to six real product benefits, one per line.")
    result["benefits"] = [text(b, "Each product benefit", 120) for b in benefits]
    if result["url"]:
        address = result["url"]
        parsed = urlparse(address if "://" in address else "https://" + address)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
            raise StudioError("Use a public website address without credentials.")
        if any(c.isspace() for c in address) or ":" in address and "://" not in address:
            raise StudioError("Use a website such as example.com or https://example.com.")
    return result


def shorten(value: str, maximum: int) -> str:
    if len(value) <= maximum:
        return value
    return value[: maximum - 1].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def narration_word_budget(duration: float) -> int:
    """Give each scene a concise line without creating an oversized dead gap.

    The previous two-words-per-second budget made template narration much
    shorter than its visual window.  This keeps a small boundary cushion while
    targeting a natural short-form-ad pace.
    """
    return max(3, int((duration - .35) * 2.4))


def spoken_line(headline: str, body: str, budget: int) -> str:
    """Build a useful template line from the visible headline and supporting copy."""
    source = f"{headline}. {body}".strip()
    words = source.split()[:budget]
    # Do not end a generated line on a dangling preposition/article after the
    # budget cut; that sounds especially unfinished in TTS.
    trailing = {"a", "an", "and", "for", "in", "of", "on", "one", "our", "the", "to", "with", "your"}
    while len(words) > 1 and words[-1].rstrip(".,;:").casefold() in trailing:
        words.pop()
    return " ".join(words).rstrip(".,;:") + "."


def template_storyboard(brief: dict) -> list[dict]:
    """An explicit non-AI draft: use supplied facts, never fabricate metrics or endorsements."""
    total = brief["duration"]
    durations = [round(total * f, 2) for f in (0.2, 4 / 15, 1 / 3)]
    durations.append(round(total - sum(durations), 2))
    benefits = brief["benefits"]
    intro = f"Meet {brief['name']}"
    entries = [
        (intro, shorten(brief["description"], 155)),
        (shorten(benefits[0], 70), shorten(benefits[1] if len(benefits) > 1 else brief["description"], 155)),
        (shorten(f"For {brief['audience']}", 70), shorten(benefits[2] if len(benefits) > 2 else benefits[-1], 155)),
        (brief["cta"], brief["url"] or brief["name"]),
    ]
    if brief["template"] == "problem_solution":
        entries[:3] = [
            (shorten(brief["problem"], 70), shorten(f"For {brief['audience']}", 155)),
            (intro, shorten(brief["description"], 155)),
            (shorten(benefits[0], 70), shorten(benefits[1] if len(benefits) > 1 else brief["description"], 155)),
        ]
    scenes = []
    for kind, (headline, body), duration in zip(KINDS, entries, durations):
        budget = narration_word_budget(duration)
        narration = spoken_line(headline, body, budget)
        scenes.append(dict(kind=kind, headline=headline, body=body, narration=narration, duration=duration))
    return validate_scenes(scenes, total)


def validate_scenes(raw, total: float) -> list[dict]:
    if not isinstance(raw, list) or len(raw) != 4:
        raise StudioError("A storyboard needs exactly four scenes.")
    scenes = []
    for index, (scene, kind) in enumerate(zip(raw, KINDS), 1):
        if not isinstance(scene, dict) or scene.get("kind") != kind:
            raise StudioError(f"Scene {index} must keep its type: {kind}.")
        try:
            if isinstance(scene.get("duration"), bool):
                raise ValueError
            duration = float(scene["duration"])
        except (ValueError, TypeError, KeyError):
            raise StudioError(f"Scene {index} needs a numeric duration.") from None
        if not math.isfinite(duration) or not 2 <= duration <= 12:
            raise StudioError(f"Scene {index} must last between 2 and 12 seconds.")
        scenes.append({"kind": kind, "headline": text(scene.get("headline", ""), f"Scene {index} headline", 72),
                       "body": text(scene.get("body", ""), f"Scene {index} supporting text", 160, False),
                       "narration": text(scene.get("narration", ""), f"Scene {index} voiceover", 260, False),
                       "duration": round(duration, 3)})
    if abs(sum(s["duration"] for s in scenes) - total) > 0.005:
        raise StudioError(f"Scene durations must add up to {total:g} seconds; currently {sum(s['duration'] for s in scenes):g}.")
    return scenes


def timeline(scenes: list[dict]) -> list[dict]:
    at = 0.0
    result = []
    for scene in scenes:
        result.append({**scene, "start": round(at, 3), "end": round(at + scene["duration"], 3)})
        at += scene["duration"]
    return result


def project_rows(project: dict) -> list[list]:
    return [[s[k] for k in ("kind", "headline", "body", "narration", "duration")] for s in project["scenes"]]
