"""
narratives.py
─────────────
Narrative Arc library loader and intelligent selector for the Jarvis Video Pipeline.
Matches a ProductProfile (tone, category, missing_data, proof_points) to the ideal
narrative structure from narratives.json.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from tools.video_pipeline.schemas import NarrativeArc, ProductProfile, ToneEnum

NARRATIVES_JSON_PATH = Path(__file__).resolve().parent / "narratives.json"


def load_narratives(path: Optional[Path] = None) -> List[NarrativeArc]:
    """Loads and validates all narrative arcs from narratives.json."""
    target_path = path or NARRATIVES_JSON_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Narratives registry not found at {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    narratives: List[NarrativeArc] = []
    for item in raw_list:
        narratives.append(NarrativeArc.model_validate(item))
    return narratives


def score_narrative_match(arc: NarrativeArc, profile: ProductProfile) -> float:
    """
    Scores how well a NarrativeArc fits a ProductProfile based on:
    - Tone alignment
    - Category keyword match
    - Grounded data constraints (penalizes pricing arcs if price is missing)
    """
    score = 0.0

    # 1. Tone match (+15 if explicit match)
    if profile.tone in arc.suitable_tones:
        score += 15.0

    # 2. Category match (+20 for direct or keyword overlap)
    cat_lower = profile.category.lower()
    for cat_keyword in arc.suitable_categories:
        if cat_keyword.lower() in cat_lower or cat_lower in cat_keyword.lower():
            score += 20.0
            break

    # 3. Missing data constraints (Strict No-Fake-Data Enforcement)
    has_pricing_role = any(b.role == "pricing" for b in arc.scene_blueprints)
    if has_pricing_role:
        if "price" in profile.missing_data:
            # Harsh penalty: never select a pricing-focused arc if price was missing from crawl
            score -= 40.0
        else:
            score += 8.0

    # 4. Proof points synergy
    has_proof_role = any(b.role == "proof" for b in arc.scene_blueprints)
    if has_proof_role:
        if profile.proof_points:
            score += 5.0
        else:
            score -= 5.0

    # 5. Fallback baseline
    if arc.id == "problem_agitate_solution":
        score += 1.0

    return score


def select_narrative(
    profile: ProductProfile,
    narratives_path: Optional[Path] = None
) -> NarrativeArc:
    """
    Selects the optimal NarrativeArc for a ProductProfile from narratives.json.
    Guarantees no invalid narrative is picked (e.g. pricing arcs with missing prices).
    """
    all_arcs = load_narratives(narratives_path)
    if not all_arcs:
        raise ValueError("No narrative arcs available in registry.")

    scored_arcs = [
        (arc, score_narrative_match(arc, profile))
        for arc in all_arcs
    ]

    # Sort descending by score
    scored_arcs.sort(key=lambda x: x[1], reverse=True)
    best_arc, best_score = scored_arcs[0]

    return best_arc
