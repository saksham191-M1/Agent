"""Deterministic natural-language intake for one-off product ads.

The prompt intake deliberately does not call a provider or invent missing
facts.  It accepts a compact labelled brief (and a few sentence-level
conveniences), returns the facts it can identify, and tells the caller which
facts still need human input before a storyboard is created.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .models import StudioError, validate_brief


MAX_PROMPT_LENGTH = 4000

_DEFAULTS = {
    "cta": "Explore the product",
    "url": "",
    "color": "#a78bfa",
    "template": "spotlight",
    "aspect": "9:16",
    "duration": 20,
    "tone": "Confident",
    "language": "English",
}

_LABELS = (
    "target audience",
    "call to action",
    "product description",
    "brand color",
    "product name",
    "description",
    "audience",
    "benefits",
    "benefit",
    "problem",
    "cta",
    "website",
    "url",
    "color",
    "duration",
    "format",
    "aspect",
    "tone",
    "language",
    "template",
    "product",
    "name",
)

# Longer labels must win over their shorter prefixes (for example, product
# description before product). Values can span lines until the next label.
_LABEL_RE = re.compile(
    r"(?im)(?<!\w)(?P<label>" + "|".join(re.escape(label) for label in _LABELS) + r")\s*[:=-]\s*"
)


@dataclass(frozen=True)
class PromptBrief:
    """The result of parsing a user's ad request."""

    brief: dict
    missing: tuple[str, ...]
    errors: tuple[str, ...]
    complete: bool
    message: str


def _clean(value: str) -> str:
    return " ".join(value.replace("\r", " ").split()).strip(" ,;.-")


def _labelled_values(prompt: str) -> dict[str, str]:
    matches = list(_LABEL_RE.finditer(prompt))
    values: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(prompt)
        value = prompt[match.end():end].strip(" \t\r\n,;")
        key = re.sub(r"\s+", "_", match.group("label").casefold())
        # Keep the first explicit value. This prevents a trailing example from
        # silently replacing facts the user already supplied.
        values.setdefault(key, value)
    return values


def _first(values: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = _clean(values.get(key, ""))
        if value:
            return value
    return ""


def _benefits(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\n+|;|\|", value)
    if len(parts) == 1:
        parts = re.split(r"\s*,\s*", value)
    result = []
    for part in parts:
        item = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", part)
        item = _clean(item)
        if item and item.casefold() not in {existing.casefold() for existing in result}:
            result.append(item)
    return result[:6]


def _sentence_fallback(prompt: str, values: dict[str, str]) -> dict[str, str]:
    """Recover a few natural sentence forms without guessing claims."""
    result = dict(values)
    if not _first(result, "name", "product_name", "product"):
        match = re.search(
            r"\b(?:ad|video)\s+for\s+([A-Za-z0-9][\w&.' -]{0,50}?)(?=\s*(?:[,.;]|\b(?:it|that|which)\b))",
            prompt,
            re.IGNORECASE,
        )
        if match:
            result["name"] = _clean(match.group(1))

    if not _first(result, "description", "product_description"):
        match = re.search(
            r"\b(?:it|the product)\s+(?:helps?|offers?|provides?|connects?|lets?|allows?)\s+([^.;\n]+)",
            prompt,
            re.IGNORECASE,
        )
        if match:
            result["description"] = _clean(match.group(0))

    audience_value = _first(result, "audience", "target_audience")
    if audience_value:
        result["audience"] = _clean(re.split(
            r"\.\s+(?:benefits?|cta|call to action|website|duration|format)\b",
            audience_value,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0])
    else:
        matches = re.findall(
            r"\b(?:target audience|audience is|made for|built for)\s*[:=-]?\s*([^.;\n]+)",
            prompt,
            re.IGNORECASE,
        )
        if matches:
            result["audience"] = _clean(matches[-1])

    if not _first(result, "benefits", "benefit"):
        match = re.search(r"\bbenefits?\s+include\s+([^.;\n]+)", prompt, re.IGNORECASE)
        if match:
            result["benefits"] = match.group(1)

    if not _first(result, "cta", "call_to_action"):
        match = re.search(r"\b(?:cta|call to action)\s+is\s+([^.;\n]+)", prompt, re.IGNORECASE)
        if match:
            result["cta"] = _clean(match.group(1))
    return result


def _options(prompt: str, values: dict[str, str], brief: dict) -> None:
    duration_match = re.search(r"\b(15|20|30)\s*[- ]?(?:seconds?|secs?|s)\b", prompt, re.IGNORECASE)
    if duration_match:
        brief["duration"] = int(duration_match.group(1))

    format_value = _first(values, "format", "aspect").casefold()
    if format_value in {"vertical", "portrait", "9:16"} or re.search(r"\bvertical\b|\bportrait\b|9:16", prompt, re.IGNORECASE):
        brief["aspect"] = "9:16"
    elif format_value in {"landscape", "widescreen", "16:9"} or re.search(r"\blandscape\b|\bwidescreen\b|16:9", prompt, re.IGNORECASE):
        brief["aspect"] = "16:9"
    elif format_value in {"square", "1:1"} or re.search(r"\bsquare\b|1:1", prompt, re.IGNORECASE):
        brief["aspect"] = "1:1"

    for tone in ("Confident", "Friendly", "Bold"):
        if _first(values, "tone").casefold() == tone.casefold() or re.search(rf"\b{tone}\b", prompt, re.IGNORECASE):
            brief["tone"] = tone
            break
    for language in ("Hindi", "Hinglish", "English"):
        if _first(values, "language").casefold() == language.casefold() or re.search(rf"\b{language}\b", prompt, re.IGNORECASE):
            brief["language"] = language
            break

    template = _first(values, "template").casefold()
    if template in {"problem_solution", "problem-solution", "problem solution"} or re.search(r"problem\s*(?:→|->|to)\s*solution", prompt, re.IGNORECASE):
        brief["template"] = "problem_solution"

    color = _first(values, "color", "brand_color")
    color_match = re.search(r"#[0-9a-fA-F]{6}\b", color or prompt)
    if color_match:
        brief["color"] = color_match.group(0)

    url = _first(values, "website", "url")
    if url:
        brief["url"] = url
    else:
        url_match = re.search(r"https?://[^\s,;]+|\b(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s,;]*)?", prompt)
        if url_match:
            brief["url"] = url_match.group(0).rstrip(".")


def parse_ad_prompt(prompt: str) -> PromptBrief:
    """Parse a user ad request without a network or model call.

    Labeled input is the reliable form and is shown in the UI example. A few
    natural forms such as ``Create a 15-second ad for Forma`` are accepted as
    conveniences, but missing product facts are always reported to the user.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise StudioError("Describe the product and the ad you want first.")
    prompt = prompt.strip()
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise StudioError(f"Keep the ad request under {MAX_PROMPT_LENGTH} characters.")

    values = _sentence_fallback(prompt, _labelled_values(prompt))
    brief = dict(_DEFAULTS)
    brief.update({
        "name": _first(values, "name", "product_name", "product"),
        "description": _first(values, "description", "product_description"),
        "audience": _first(values, "audience", "target_audience"),
        "problem": _first(values, "problem"),
        "benefits": "\n".join(_benefits(_first(values, "benefits", "benefit"))),
        "cta": _first(values, "cta", "call_to_action") or _DEFAULTS["cta"],
    })
    _options(prompt, values, brief)

    missing = []
    if not brief["name"]:
        missing.append("product name")
    if not brief["description"]:
        missing.append("product description")
    if not brief["audience"]:
        missing.append("target audience")
    if not brief["benefits"]:
        missing.append("at least one verified product benefit")
    if brief["template"] == "problem_solution" and not brief["problem"]:
        missing.append("the real customer problem for Problem → solution")

    errors = []
    validated = brief
    if not missing:
        try:
            validated = validate_brief(brief)
        except StudioError as exc:
            errors.append(str(exc))

    if missing or errors:
        requested = ", ".join(missing + errors)
        message = (
            "I need " + requested + ". Add labeled facts such as "
            "Product, Description, Audience, Benefits, and CTA; no unsupported claims will be invented."
        )
    else:
        message = "Brief extracted. Review the facts and render the editable storyboard."
    return PromptBrief(validated, tuple(missing), tuple(errors), not missing and not errors, message)
