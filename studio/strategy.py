"""Contracts for the creative-director pass before scene copy is written."""
from __future__ import annotations

import re

from .models import StudioError, text

HOOK_TYPES = ("pain_recognition", "curiosity", "contrarian", "transformation", "audience_callout", "specific_situation")
PROOF_METHODS = ("product_workflow", "screen_recording", "product_image", "benefit_card", "before_after")


def _clean_list(value, label: str, maximum: int, minimum: int, item_maximum: int) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise StudioError(f"The strategist returned an invalid {label} list.")
    return [text(item, f"Strategy {label}", item_maximum) for item in value]


def _words(value: str) -> set[str]:
    return set(re.findall(r"\w+", value.casefold()))


def validate_strategy(raw: dict, brief: dict, recent_hooks: list[str] | None = None) -> dict:
    if not isinstance(raw, dict):
        raise StudioError("The creative strategist returned an invalid object.")
    hooks = _clean_list(raw.get("hook_options"), "hook options", 5, 3, 100)
    selected = text(raw.get("selected_hook", ""), "Selected hook", 100)
    if selected not in hooks:
        raise StudioError("The strategist's selected hook was not one of its hook options.")
    hook_type = raw.get("hook_type")
    if hook_type not in HOOK_TYPES:
        raise StudioError(f"The strategist returned an unsupported hook type: {hook_type}.")
    proof = raw.get("proof_method")
    if proof not in PROOF_METHODS:
        raise StudioError(f"The strategist returned an unsupported proof method: {proof}.")
    lead = text(raw.get("lead_benefit", ""), "Lead benefit", 120)
    if lead not in brief["benefits"]:
        raise StudioError("The strategist selected a benefit that was not in the approved product profile.")
    arc = _clean_list(raw.get("emotional_arc"), "emotional arc", 4, 4, 40)
    recent = [_words(h) for h in (recent_hooks or []) if isinstance(h, str)]
    selected_words = _words(selected)
    if selected.casefold() in {h.casefold() for h in (recent_hooks or [])}:
        raise StudioError("The strategist repeated a recent hook.")
    if any(selected_words and len(selected_words & old) / max(1, len(selected_words)) >= .85 for old in recent):
        raise StudioError("The strategist's hook is too close to a recent hook.")
    generic = {"meet " + brief["name"].casefold(), brief["name"].casefold(), "discover " + brief["name"].casefold()}
    if selected.casefold().strip(" .!?\u2026") in generic:
        raise StudioError("The strategist selected a generic product-introduction hook.")
    if len(set(h.casefold() for h in hooks)) != len(hooks):
        raise StudioError("The strategist returned duplicate hook options.")
    return {
        "concept_name": text(raw.get("concept_name", ""), "Concept name", 100),
        "core_promise": text(raw.get("core_promise", ""), "Core promise", 180),
        "audience_insight": text(raw.get("audience_insight", ""), "Audience insight", 220),
        "hook_type": hook_type,
        "hook_options": hooks,
        "selected_hook": selected,
        "emotional_arc": arc,
        "lead_benefit": lead,
        "proof_method": proof,
        "visual_strategy": text(raw.get("visual_strategy", ""), "Visual strategy", 240),
        "cta_strategy": text(raw.get("cta_strategy", ""), "CTA strategy", 180),
        "risk_notes": _clean_list(raw.get("risk_notes", []), "risk notes", 6, 0, 180),
    }


def deterministic_strategy(brief: dict, direction: dict | None = None, recent_hooks: list[str] | None = None) -> dict:
    """Offline strategy used only when the user intentionally chooses Template copy."""
    direction = direction or {}
    angle = direction.get("angle", "benefit_first")
    if angle == "problem_solution" and brief.get("problem"):
        hook = brief["problem"].rstrip(".!?") + "?"
        hook_type = "pain_recognition"
    elif angle == "audience_first":
        hook = f"For {brief['audience']}: a clearer way to move forward."
        hook_type = "audience_callout"
    else:
        hook = f"What if {brief['benefits'][0].rstrip('.')}?"
        hook_type = "curiosity"
    if hook.casefold() in {h.casefold() for h in (recent_hooks or [])}:
        hook = f"A clearer way to {brief['benefits'][0].rstrip('.').lower()}."
    return {
        "concept_name": direction.get("label", "Benefit-led product story"),
        "core_promise": brief["benefits"][0],
        "audience_insight": f"{brief['audience']} need a clear next step.",
        "hook_type": hook_type, "hook_options": [hook, f"Still struggling with {brief['problem'].rstrip('.')}?" if brief.get("problem") else f"See what {brief['name']} changes.", f"Make {brief['benefits'][0].rstrip('.').lower()} easier."],
        "selected_hook": hook, "emotional_arc": ["friction", "recognition", "relief", "action"],
        "lead_benefit": direction.get("lead_benefit", brief["benefits"][0]), "proof_method": "product_workflow",
        "visual_strategy": "Use the supplied product asset or a factual benefit card; add no invented UI.",
        "cta_strategy": f"Connect {brief['cta']} to the stated benefit.", "risk_notes": ["Review all product claims before publishing."],
    }
