"""Deterministic gates for AI-generated advertising copy."""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from .models import StudioError, narration_word_budget, validate_scenes

_GENERIC_HOOKS = {"meet", "discover", "introducing", "welcome to"}
_UNSUPPORTED = re.compile(r"\b(best|#1|number one|revolutionary|guaranteed|guarantee|award[- ]winning|instant(?:ly)?|effortless(?:ly)?|free trial|save \d+%|\d+% faster)\b", re.I)


def _normalize(value: str) -> str:
    return re.sub(r"\W+", " ", value.casefold()).strip()


def evaluate_script(scenes: list[dict], brief: dict, strategy: dict, recent_scripts: list[list[dict]] | None = None) -> dict:
    errors, warnings = [], []
    validate_scenes(scenes, brief["duration"])
    hook = scenes[0]["headline"].strip()
    if _normalize(hook) in {_normalize(f"Meet {brief['name']}"), _normalize(f"Discover {brief['name']}"), _normalize(brief["name"])}:
        errors.append("The opening hook is a generic product introduction; use a problem, question, audience callout, or transformation.")
    if strategy.get("selected_hook") and _normalize(hook) != _normalize(strategy["selected_hook"]):
        errors.append("The first scene does not use the strategist's selected hook.")
    full_text = " ".join(f"{s['headline']} {s['body']} {s['narration']}" for s in scenes)
    if _UNSUPPORTED.search(full_text):
        errors.append("The script contains a high-risk promise or unsupported marketing superlative.")
    benefit_terms = set(re.findall(r"\w+", " ".join(brief["benefits"]).casefold()))
    script_terms = set(re.findall(r"\w+", full_text.casefold()))
    if not benefit_terms.intersection(script_terms):
        errors.append("The script does not clearly communicate an approved product benefit.")
    if not any(_normalize(s["narration"]) != _normalize(s["headline"]) for s in scenes[:3]):
        errors.append("Narration only repeats headlines; it needs a connected spoken explanation.")
    if _normalize(scenes[-1]["headline"]) != _normalize(brief["cta"]) and _normalize(brief["cta"]) not in _normalize(scenes[-1]["body"]):
        warnings.append("The final CTA does not exactly match the approved CTA.")
    if len({_normalize(s["headline"]) for s in scenes}) < 4:
        errors.append("Two or more scenes have the same headline.")
    for scene in scenes:
        budget = narration_word_budget(scene["duration"])
        count = len(scene["narration"].split())
        if not count or count > budget:
            errors.append(f"{scene['kind']} narration has {count} words; write 1–{budget} words for its {scene['duration']:g}s window.")
        else:
            minimum = max(3, int((scene["duration"] - .5) * 1.35))
            if count < minimum:
                errors.append(f"{scene['kind']} narration has {count} words; add a little more spoken substance (at least {minimum} words) so the scene does not feel empty.")
    for previous in (recent_scripts or [])[-8:]:
        current = _normalize(" ".join(s["headline"] + " " + s["body"] for s in scenes[:3]))
        old = _normalize(" ".join(s["headline"] + " " + s["body"] for s in previous[:3]))
        if SequenceMatcher(None, current, old).ratio() > .92:
            errors.append("The script is too similar to a recent ad.")
            break
    score = max(0, 100 - 22 * len(errors) - 5 * len(warnings))
    return {"score": score, "errors": errors, "warnings": warnings, "passed": not errors}


def quality_feedback(result: dict) -> str:
    return "\n".join(["Fix the following script-quality failures without inventing facts:", *[f"- {e}" for e in result["errors"]],
                     *[f"- Warning: {w}" for w in result["warnings"]]])


def require_quality(scenes: list[dict], brief: dict, strategy: dict, recent_scripts=None) -> dict:
    result = evaluate_script(scenes, brief, strategy, recent_scripts)
    if not result["passed"]:
        raise StudioError("Script quality check failed: " + " ".join(result["errors"]))
    return result
