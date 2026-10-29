"""Bounded creative rotation using reviewed facts, not random invented claims."""
from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher

from .models import KINDS, StudioError, narration_word_budget, shorten, spoken_line, validate_scenes

ANGLES = {
    "benefit_first": "Lead with one concrete benefit",
    "audience_first": "Speak to the intended audience",
    "product_reveal": "Introduce the product and its purpose",
    "feature_tour": "Tour the supplied product benefits",
    "single_feature": "Focus the story on a single capability",
    "problem_solution": "Connect the stated problem to the product",
}
LOOKS = ("glow", "editorial", "minimal")


def words(value: str) -> set[str]:
    return set(re.findall(r"\w+", value.casefold()))


def _copy_text(scenes: list[dict]) -> str:
    return " ".join(" ".join((s["headline"], s["body"], s["narration"])) for s in scenes[:3]).casefold()


def signature(scenes: list[dict], plan: dict) -> str:
    payload = {"copy": re.sub(r"\W+", " ", _copy_text(scenes)).strip(), "look": plan["look"], "template": plan["template"]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def duplicate_reason(scenes: list[dict], plan: dict, history: list[dict]) -> str | None:
    current = signature(scenes, plan)
    if history and _copy_text(scenes) == _copy_text(history[-1]["scenes"]):
        return "This storyboard repeats the previous ad's copy despite a new creative direction."
    for past in history:
        previous_plan = past.get("creative") or {}
        if not previous_plan or not past.get("scenes"):
            continue
        if current == signature(past["scenes"], previous_plan):
            return "This copy and visual direction duplicate an existing ad."
    for past in history[-7:]:
        previous_plan = past.get("creative") or {}
        if previous_plan.get("look") == plan["look"] and previous_plan.get("angle") == plan["angle"]:
            if SequenceMatcher(None, _copy_text(scenes), _copy_text(past["scenes"])).ratio() > .94:
                return "This draft is too close to a recent ad with the same angle and visual direction."
    return None


def rotated_brief(brief: dict, plan: dict) -> dict:
    benefits = list(brief["benefits"])
    index = plan["benefit_index"]
    return {**brief, "benefits": benefits[index:] + benefits[:index], "template": plan["template"]}


def variant_storyboard(brief: dict, plan: dict) -> list[dict]:
    """The input brief already has its benefits ordered for this creative plan."""
    benefits, name = brief["benefits"], brief["name"]
    first = benefits[0]
    second = benefits[1] if len(benefits) > 1 else brief["description"]
    third = benefits[2] if len(benefits) > 2 else first
    audience = f"For {brief['audience']}"
    introduction = f"Meet {name}"
    variations = {
        "benefit_first": [(first, audience), (introduction, brief["description"]), (second, third)],
        "audience_first": [(audience, first), (first, brief["description"]), (f"Discover {name}", second)],
        "product_reveal": [(introduction, brief["description"]), (first, second), (audience, third)],
        "feature_tour": [(f"Inside {name}", first), (second, brief["description"]), (third, audience)],
        "single_feature": [(first, brief["description"]), (f"Explore {name}", first), (audience, second)],
        "problem_solution": [(brief["problem"], audience), (introduction, brief["description"]), (first, second)],
    }
    entries = variations[plan["angle"]] + [(brief["cta"], brief["url"] or name)]
    patterns = {"glow": (0.2, 0.267, 0.333), "editorial": (0.25, 0.3, 0.25), "minimal": (0.2, 0.3, 0.3)}
    total = brief["duration"]
    durations = [round(total * fraction, 3) for fraction in patterns[plan["look"]]]
    durations.append(round(total - sum(durations), 3))
    scenes = []
    for kind, (headline, body), duration in zip(KINDS, entries, durations):
        headline, body = shorten(headline, 70), shorten(body, 155)
        # Template mode is intentionally factual and keeps input-language text; it does not invent a translation.
        budget = narration_word_budget(duration)
        spoken = spoken_line(headline, body, budget)
        scenes.append({"kind": kind, "headline": headline, "body": body, "narration": spoken, "duration": duration})
    return validate_scenes(scenes, total)


def select_plan(brief: dict, history: list[dict], goal: str = "") -> dict:
    used = {p.get("creative", {}).get("key") for p in history}
    recent = [p.get("creative", {}) for p in history[-2:]]
    goal_words = words(goal) - {"the", "and", "for", "with", "this", "that", "video", "ad", "focus"}
    candidates = []
    for angle_index, angle in enumerate(ANGLES):
        if angle == "problem_solution" and not brief.get("problem"):
            continue
        for benefit_index, benefit in enumerate(brief["benefits"]):
            fact_key = hashlib.sha256(benefit.casefold().encode()).hexdigest()[:12]
            for look_index, look in enumerate(LOOKS):
                key = f"{angle}:{fact_key}:{look}"
                if key in used:
                    continue
                plan = {"key": key, "angle": angle, "label": ANGLES[angle], "benefit_index": benefit_index,
                        "lead_benefit": benefit, "look": look,
                        "template": "problem_solution" if angle == "problem_solution" else "spotlight",
                        "goal": goal}
                scenes = variant_storyboard(rotated_brief(brief, plan), plan)
                if duplicate_reason(scenes, plan, history):
                    continue
                if history and scenes[0]["headline"].casefold() == history[-1]["scenes"][0]["headline"].casefold():
                    continue
                repeat_penalty = sum(8 * (p.get("angle") == angle) + 4 * (p.get("lead_benefit") == benefit)
                                     + 2 * (p.get("look") == look) for p in recent)
                relevance = len(goal_words & words(benefit))
                candidates.append(((repeat_penalty - relevance * 10, angle_index + look_index + benefit_index,
                                    benefit_index, look_index, angle_index), plan))
    if not candidates:
        raise StudioError("The non-repeating creative pool for these facts is exhausted. Add a genuinely new benefit, customer problem, or campaign material rather than publishing another duplicate.")
    return min(candidates, key=lambda item: item[0])[1]
