"""
storyboard_validator.py
────────────────────────
Validates that generated storyboards do not contain foreign brands,
unsupported numbers, or invalid pacing before passing to the assembler.
"""

import re
from typing import List, Tuple
from tools.video_pipeline.schemas import ProductProfile, StoryboardDirectorSpec


KNOWN_BRANDS = [
    "swiggy", "zomato", "zerodha", "flipkart", "supabase", "prisma", "resend", "linear"
]


def validate_storyboard(profile: ProductProfile, storyboard: StoryboardDirectorSpec) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    
    # 1. Total duration and scene bounds
    if not (10.0 <= storyboard.total_seconds <= 40.0):
        errors.append(f"Total seconds {storyboard.total_seconds} out of bounds (10.0 - 40.0s)")
    if not (3 <= storyboard.scene_count <= 8):
        errors.append(f"Scene count {storyboard.scene_count} out of bounds (3 - 8)")
        
    calc_sum = sum(s.duration_seconds for s in storyboard.scenes)
    if abs(calc_sum - storyboard.total_seconds) > 0.05:
        errors.append(f"Scene durations sum {calc_sum:.2f} does not match total {storyboard.total_seconds:.2f}")

    # 2. Extract profile proof points text
    profile_proofs = " ".join([p.text.lower() for p in profile.proof_points] + [profile.core_differentiator.lower()])
    current_brand = profile.name.lower()

    # 3. Scene checks
    for idx, s in enumerate(storyboard.scenes, start=1):
        # Role check
        if idx == 1 and s.layout == "cta":
            errors.append(f"Scene 1 cannot have layout 'cta'")
        if idx == len(storyboard.scenes) and s.layout not in ["cta", "hero-type", "card"]:
            errors.append(f"Final scene must be cta or hero-type")

        # Foreign brand check
        scene_text = f"{s.kinetic_text} {s.voiceover}".lower()
        for b in KNOWN_BRANDS:
            if b != current_brand and re.search(rf"\b{b}\b", scene_text):
                errors.append(f"Scene {idx} contains foreign brand '{b}' in copy")

        # Words/sec pacing check (~2.4 wps, flag if > 3.2 wps)
        word_count = len(s.voiceover.split())
        wps = word_count / max(0.5, s.duration_seconds)
        if wps > 3.2:
            errors.append(f"Scene {idx} voiceover pacing too fast ({wps:.2f} words/sec, max 3.2)")

        # Unsupported number check
        numbers = re.findall(r"\b(?:\d[\d,.]*|\d+%|million|billion|lakh|crore)\b", scene_text, re.IGNORECASE)
        for num in numbers:
            num_clean = num.lower()
            if num_clean in ["1", "2", "3", "4", "5", "6", "7"]:
                continue
            if num_clean not in profile_proofs:
                errors.append(f"Scene {idx} contains unverified number/metric '{num}' not in profile proof points")

    return len(errors) == 0, errors
