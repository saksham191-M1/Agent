"""
Curated viral hooks, comedy setups, and psychological patterns for 10-15s content.
"""
from typing import Dict, List, Any
from jarvis.ai_content.scripts.shorts.contracts import ContentStyle, HookArchetype


HOOK_FORMULAS: Dict[HookArchetype, List[Dict[str, str]]] = {
    HookArchetype.PATTERN_INTERRUPT: [
        {
            "spoken_template": "Wait, did you really think {concept} was safe?",
            "kinetic_text": "WAIT... WHAT?!",
            "camera": "explosive_push",
            "sfx": "record_scratch",
            "visual_style": "Dramatic sudden macro zoom or shattered screen effect"
        },
        {
            "spoken_template": "Stop scrolling if you use {concept}.",
            "kinetic_text": "STOP RIGHT NOW.",
            "camera": "explosive_push",
            "sfx": "vine_boom",
            "visual_style": "High-velocity whip pan into glowing object"
        }
    ],
    HookArchetype.CONTRARIAN: [
        {
            "spoken_template": "Everything you know about {concept} is wrong.",
            "kinetic_text": "YOU'RE DOING IT WRONG.",
            "camera": "explosive_push",
            "sfx": "cinematic_boom",
            "visual_style": "Inverted color grade flipping into sharp clarity"
        },
        {
            "spoken_template": "Why 99% of people fail with {concept} in 2026.",
            "kinetic_text": "THE 99% MISTAKE.",
            "camera": "explosive_push",
            "sfx": "cinematic_boom",
            "visual_style": "Red warning glitch with dark moody backdrop"
        }
    ],
    HookArchetype.CURIOSITY_GAP: [
        {
            "spoken_template": "This one hidden {concept} trick feels completely illegal.",
            "kinetic_text": "FEELS ILLEGAL.",
            "camera": "explosive_push",
            "sfx": "glitch",
            "visual_style": "Holographic code or secret vault unlocking"
        },
        {
            "spoken_template": "Nobody talks about this {concept} feature, but it changes everything.",
            "kinetic_text": "NOBODY TALKS ABOUT THIS.",
            "camera": "explosive_push",
            "sfx": "whoosh",
            "visual_style": "Shadowed object stepping into violet spotlight"
        }
    ],
    HookArchetype.ABSURD_COMEDY: [
        {
            "spoken_template": "POV: You trusted {concept} for 5 seconds.",
            "kinetic_text": "NEVER AGAIN.",
            "camera": "handheld_shake",
            "sfx": "vine_boom",
            "visual_style": "Chaotic comical situation with exaggerated reaction"
        },
        {
            "spoken_template": "When your {concept} gets sentient and starts roasting you.",
            "kinetic_text": "IT STARTED TALKING.",
            "camera": "explosive_push",
            "sfx": "pop",
            "visual_style": "Inanimate object staring blankly while lights flicker"
        }
    ],
    HookArchetype.RELATABLE_PAIN: [
        {
            "spoken_template": "That visceral dread when {concept} breaks at 2 AM.",
            "kinetic_text": "2 AM NIGHTMARE.",
            "camera": "handheld_shake",
            "sfx": "cinematic_boom",
            "visual_style": "Glowing red monitors reflecting on panicked face"
        }
    ]
}


STYLE_BLUEPRINTS: Dict[ContentStyle, Dict[str, Any]] = {
    ContentStyle.PRODUCT_AD: {
        "preferred_hook": HookArchetype.CONTRARIAN,
        "music": "ambient_electronic_build",
        "pacing": "crisp_authoritative",
        "structure": [
            ("hook", 2.5),
            ("escalation", 3.5),
            ("climax", 4.5),
            ("loop_cta", 2.0)
        ]
    },
    ContentStyle.COMEDY_SKETCH: {
        "preferred_hook": HookArchetype.ABSURD_COMEDY,
        "music": "quirky_upbeat_bounce",
        "pacing": "fast_comedic_timing",
        "structure": [
            ("hook", 2.5),
            ("escalation", 4.0),
            ("climax", 4.0),
            ("loop_cta", 2.0)
        ]
    },
    ContentStyle.CURIOSITY_LIFEHACK: {
        "preferred_hook": HookArchetype.CURIOSITY_GAP,
        "music": "future_bass_pulsing",
        "pacing": "high_energy_revelation",
        "structure": [
            ("hook", 2.0),
            ("escalation", 4.0),
            ("climax", 4.5),
            ("loop_cta", 2.0)
        ]
    },
    ContentStyle.RELATABLE_POV: {
        "preferred_hook": HookArchetype.RELATABLE_PAIN,
        "music": "lofi_ironic_chill",
        "pacing": "conversational_deadpan",
        "structure": [
            ("hook", 2.5),
            ("escalation", 4.0),
            ("climax", 4.0),
            ("loop_cta", 2.0)
        ]
    }
}
