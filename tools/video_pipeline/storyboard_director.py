"""
storyboard_director.py
──────────────────────
Dynamic storyboard generator and critique gate for the Director AI video pipeline.
Executes:
1. Director Call 2 (Storyboard Generation) using prompts/storyboard.md and selected NarrativeArc.
2. Director Call 3 (Critique & Revision Gate) using prompts/critique.md to reject hallucinated claims
   and strip headline punctuation.
3. Deterministic code-level sanitization:
   - Strips terminal punctuation (., :, ;, !) from kinetic_text
   - Guarantees total_seconds == exact sum of scene durations
   - Sequences scene_id from 1 to N
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from tools.video_pipeline.director import call_director, DirectorError
from tools.video_pipeline.schemas import (
    ProductProfile,
    NarrativeArc,
    StoryboardDirectorSpec,
    SceneDirectorSpec,
    CritiqueFeedback,
    CritiqueScores,
)
from tools.video_pipeline.history import (
    record_run_history,
    append_history,
    get_recent_history,
    format_history_nudge
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _safe_str(text: Any) -> str:
    """Returns a string safe for console output across all Windows encodings."""
    try:
        return str(text).encode("ascii", errors="replace").decode("ascii")
    except Exception:
        return ""


PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
STORYBOARD_PROMPT_PATH = PROMPTS_DIR / "storyboard.md"
CRITIQUE_PROMPT_PATH = PROMPTS_DIR / "critique.md"


def load_storyboard_prompt() -> str:
    """Loads system prompt markdown for storyboard generation."""
    if STORYBOARD_PROMPT_PATH.exists():
        return STORYBOARD_PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are an expert Creative Director. Generate a high-impact, brand-authentic "
        "video ad storyboard based on the provided ProductProfile and NarrativeArc. Never invent facts."
    )


def load_critique_prompt() -> str:
    """Loads system prompt markdown for critique gate."""
    if CRITIQUE_PROMPT_PATH.exists():
        return CRITIQUE_PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are a Senior Creative Director. Rigorously critique the drafted storyboard against the "
        "ProductProfile. Check for ungrounded claims, price/rating hallucinations, and terminal punctuation."
    )


def sanitize_storyboard(
    spec: StoryboardDirectorSpec,
    arc: Optional[NarrativeArc] = None,
    profile: Optional[ProductProfile] = None
) -> StoryboardDirectorSpec:
    """
    Applies deterministic code-level rules to guarantee schema and production compliance:
    1. Strips all terminal punctuation (. , : ; ! ?) from kinetic_text headlines.
    2. Recalculates total_seconds to match the exact sum of scene duration_seconds.
    3. Normalizes scene_id to 1..N.
    4. Sets scene_count to len(scenes).
    5. Populates template and product identity metadata.
    """
    sanitized_scenes: List[SceneDirectorSpec] = []
    total_duration = 0.0

    for idx, scene in enumerate(spec.scenes, start=1):
        clean_text = scene.kinetic_text.strip()
        # Ban terminal punctuation on headlines
        clean_text = re.sub(r"[\.\:\;\!\?\,]+$", "", clean_text).strip()
        if not clean_text:
            clean_text = profile.name.upper() if profile else "EXPERIENCE"

        dur = round(float(scene.duration_seconds), 2)
        total_duration += dur

        updated_scene = scene.model_copy(update={
            "scene_id": idx,
            "duration_seconds": dur,
            "kinetic_text": clean_text
        })
        sanitized_scenes.append(updated_scene)

    exact_total = round(total_duration, 2)
    template_name = spec.selected_template or (arc.name if arc else "Dynamic Narrative")
    narrative_id = arc.id if arc else spec.narrative_type

    return spec.model_copy(update={
        "product_name": profile.name if profile else spec.product_name,
        "narrative_type": narrative_id,
        "selected_template": template_name,
        "matched_opus_category": spec.matched_opus_category or "MOTION",
        "scene_count": len(sanitized_scenes),
        "total_seconds": exact_total,
        "scenes": sanitized_scenes
    })


def generate_storyboard(
    profile: ProductProfile,
    arc: NarrativeArc,
    run_id: Optional[str] = None,
    skip_critique: bool = False
) -> StoryboardDirectorSpec:
    """
    Executes Director Call 2 (Storyboard Generation) and Director Call 3 (Critique Gate).
    Returns a strictly validated, sanitized StoryboardDirectorSpec.
    """
    print(f"\n[Director] Generating dynamic storyboard for '{_safe_str(profile.name)}' with arc '{arc.name}'...")

    # ──────────────────────────────────────────────────────────────────────────
    # Director Call 2: Storyboard Generation
    # ──────────────────────────────────────────────────────────────────────────
    storyboard_sys = load_storyboard_prompt()

    # Build structured user instructions with recent history nudge
    proofs_str = "\n".join([f"- {p.text} (Source: {p.source})" for p in profile.proof_points]) or "None extracted"
    missing_str = ", ".join(profile.missing_data) or "None"
    blueprints_str = json.dumps([b.model_dump() for b in arc.scene_blueprints], indent=2)
    history_nudge = format_history_nudge(get_recent_history(5))

    storyboard_user = f"""PRODUCT PROFILE:
- Name: {profile.name}
- Category: {profile.category}
- Tone: {profile.tone.value}
- Description: {profile.what_it_is}
- Audience: {profile.audience}
- Core Differentiator: {profile.core_differentiator}
- Ground-Truth Proof Points:
{proofs_str}
- Explicitly Missing Data (DO NOT CLAIM OR GUESS): {missing_str}
- Visual Style Hint: {profile.visual_style_hint}

SELECTED NARRATIVE ARC:
- Arc ID: {arc.id}
- Arc Name: {arc.name}
- Description: {arc.description}
- Target Duration: {arc.duration_seconds_range[0]}s - {arc.duration_seconds_range[1]}s ({arc.scene_count_range[0]}-{arc.scene_count_range[1]} scenes)
- Scene Blueprints:
{blueprints_str}
{history_nudge}
MANDATES:
1. Every scene must follow the designated role from the scene blueprints.
2. Headlines (kinetic_text) must NOT end with terminal punctuation (no periods, colons, or semicolons).
3. Do NOT invent prices, ratings, or stats not listed in proof points.
4. Total duration must be the exact sum of scene durations.
"""

    draft_storyboard = call_director(
        system=storyboard_sys,
        user=storyboard_user,
        schema=StoryboardDirectorSpec,
        step_name="storyboard",
        run_id=run_id,
        temperature=0.7
    )

    print(f"[Director] Initial storyboard generated ({len(draft_storyboard.scenes)} scenes, {draft_storyboard.total_seconds}s)")

    active_storyboard = draft_storyboard

    # ──────────────────────────────────────────────────────────────────────────
    # Director Call 3: Critique & Revision Gate
    # ──────────────────────────────────────────────────────────────────────────
    if not skip_critique:
        critique_sys = load_critique_prompt()
        draft_dump = json.dumps(draft_storyboard.model_dump(), indent=2)

        critique_user = f"""PRODUCT PROFILE GROUND TRUTH:
- Name: {profile.name}
- Proof Points:
{proofs_str}
- Missing Data (Strictly forbidden to fabricate): {missing_str}

DRAFTED STORYBOARD TO AUDIT:
{draft_dump}

INSPECTION TASKS:
1. Are there any invented facts, prices, discounts, or ratings not in proof points?
2. Does any headline in scenes[].kinetic_text end with a period, colon, or semicolon?
3. If violations are present, set passes_qa to false, explain in revision_notes, and output the complete revised_storyboard with fixes applied.
"""

        try:
            critique: CritiqueFeedback = call_director(
                system=critique_sys,
                user=critique_user,
                schema=CritiqueFeedback,
                step_name="critique",
                run_id=run_id,
                temperature=0.2
            )

            # Audit specificity & differentiator scores
            if critique.scores:
                if critique.scores.specificity < 4 or critique.scores.differentiator_use < 4:
                    print(f"[Critique Gate] [WARN] Generic script detected (specificity={critique.scores.specificity}, differentiator_use={critique.scores.differentiator_use})")
                    critique.passes_qa = False

            print(f"[Critique Gate] Passed QA: {critique.passes_qa}")
            if critique.problems:
                print(f"[Critique Gate] Problems noted: {critique.problems}")
            if critique.invented_facts_detected:
                print(f"[Critique Gate] [WARN] Invented facts caught: {critique.invented_facts_detected}")
            if critique.punctuation_violations:
                print(f"[Critique Gate] [WARN] Punctuation violations caught: {critique.punctuation_violations}")

            if not critique.passes_qa and critique.revised_storyboard:
                print("[Critique Gate] Adopting corrected revised storyboard from Critique Director.")
                active_storyboard = critique.revised_storyboard

            if run_id:
                record_run_history(
                    run_id=run_id,
                    product_name=profile.name,
                    domain="",
                    step_name="critique",
                    metadata={
                        "passes_qa": critique.passes_qa,
                        "scores": critique.scores.model_dump() if critique.scores else {},
                        "problems": critique.problems,
                        "invented_facts": critique.invented_facts_detected,
                        "punctuation_violations": critique.punctuation_violations,
                        "revision_notes": critique.revision_notes,
                        "revision_instructions": critique.revision_instructions
                    }
                )

        except Exception as e:
            print(f"[Critique Gate] [WARN] Critique step skipped or error: {_safe_str(e)}")

    # ──────────────────────────────────────────────────────────────────────────
    # Deterministic Sanitization
    # ──────────────────────────────────────────────────────────────────────────
    final_storyboard = sanitize_storyboard(active_storyboard, arc=arc, profile=profile)

    # Append creative signature to persistent history log
    append_history({
        "run_id": run_id or f"run_{profile.name.lower()[:8]}",
        "product_name": profile.name,
        "narrative_id": final_storyboard.narrative_type,
        "scene_count": len(final_storyboard.scenes),
        "total_duration_s": final_storyboard.total_seconds,
        "primitive_sequence": [s.layout for s in final_storyboard.scenes],
        "motion_profiles": [s.motion_profile for s in final_storyboard.scenes],
        "music_mood": final_storyboard.music_mood,
        "transitions": [s.transition_out for s in final_storyboard.scenes]
    })

    if run_id:
        record_run_history(
            run_id=run_id,
            product_name=profile.name,
            domain="",
            step_name="final_storyboard",
            metadata={
                "template": final_storyboard.selected_template,
                "scenes": len(final_storyboard.scenes),
                "total_seconds": final_storyboard.total_seconds,
                "headlines": [s.kinetic_text for s in final_storyboard.scenes]
            }
        )

    print(f"[Director] Final storyboard ready: {final_storyboard.selected_template} ({len(final_storyboard.scenes)} scenes, {final_storyboard.total_seconds}s)")
    return final_storyboard
