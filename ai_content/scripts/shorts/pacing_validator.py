import re
import logging
from typing import Tuple, List
from jarvis.ai_content.scripts.shorts.contracts import ShortsScriptContract, ShortScene

logger = logging.getLogger(__name__)


class RetentionScorer:
    """
    Evaluates short-form scripts (10-15s) against algorithmic retention heuristics.
    """

    @classmethod
    def score_script(cls, script: ShortsScriptContract) -> Tuple[float, List[str]]:
        score = 0.0
        breakdown = []

        # 1. Hook Speed & Brevity (Max 25 pts)
        hook = script.scenes[0]
        if hook.duration <= 2.2:
            score += 25.0
            breakdown.append("+25: Ultra-fast hook under 2.2s")
        elif hook.duration <= 2.8:
            score += 20.0
            breakdown.append("+20: Sharp hook under 2.8s")
        else:
            score += 10.0
            breakdown.append("+10: Hook duration slightly long")

        # 2. Kinetic Text Readability (Max 20 pts)
        avg_text_len = sum(len(s.kinetic_text.split()) for s in script.scenes) / len(script.scenes)
        if 2 <= avg_text_len <= 5:
            score += 20.0
            breakdown.append("+20: Ideal kinetic text length (2-5 words per shot)")
        else:
            score += 10.0
            breakdown.append("+10: Subtitle word count deviates from optimal")

        # 3. Audio SFX Impact Distribution (Max 20 pts)
        sfx_types = {s.sfx_cue for s in script.scenes}
        if len(sfx_types) >= 2 and hook.sfx_cue in ["vine_boom", "cinematic_boom", "record_scratch", "whoosh"]:
            score += 20.0
            breakdown.append("+20: High-impact opening SFX with variety")
        else:
            score += 12.0
            breakdown.append("+12: Moderate audio impact")

        # 4. Spoken Cadence & Word Count (Max 20 pts)
        total_words = sum(len(s.spoken_line.split()) for s in script.scenes)
        wps = total_words / script.total_duration
        # Sweet spot for reels/shorts is 2.3 - 2.8 words per second
        if 2.1 <= wps <= 2.9:
            score += 20.0
            breakdown.append(f"+20: Optimal spoken cadence ({wps:.1f} words/sec)")
        else:
            score += 10.0
            breakdown.append(f"+10: Cadence slightly outside sweet spot ({wps:.1f} words/sec)")

        # 5. Seamless Loop Potential (Max 15 pts)
        if script.loop_seamless:
            score += 15.0
            breakdown.append("+15: Seamless loop ending configured")
        else:
            score += 5.0

        final_score = min(100.0, max(0.0, score))
        return final_score, breakdown
