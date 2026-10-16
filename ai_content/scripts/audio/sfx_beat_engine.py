import json
import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from pathlib import Path

logger = logging.getLogger(__name__)


# --- SFX Models ---

class SFXCue(BaseModel):
    """A single sound effect event tied to a visual action."""
    timestamp: float = Field(description="Time in seconds from scene start")
    sfx_type: Literal[
        "whoosh", "impact", "pop", "click", "swoosh",
        "glass_shatter", "metal_clang", "explosion_soft",
        "digital_glitch", "power_up", "power_down",
        "typing_burst", "notification_ding",
        "ambient_drone", "rise_tension", "hit_resolve",
        "cinematic_boom", "reverse_cymbal", "tape_stop",
        "record_scratch", "vine_boom"
    ]
    intensity: Literal["subtle", "medium", "heavy"] = "medium"
    duration: float = Field(default=0.5, ge=0.1, le=5.0, description="Duration in seconds")
    trigger_action: str = Field(description="The visual action that triggers this SFX")


class SceneSFXPlan(BaseModel):
    """SFX plan for a single scene."""
    scene_id: str
    sfx_cues: List[SFXCue] = Field(default_factory=list)
    ambient_bed: Optional[str] = Field(default=None, description="Continuous ambient sound for the scene")
    ambient_volume: float = Field(default=0.3, ge=0.0, le=1.0)


class AudioMixPlan(BaseModel):
    """Complete audio plan across all scenes."""
    scenes: List[SceneSFXPlan]
    music_track: str = Field(default="ambient_electronic_build", description="Background music genre/track")
    music_volume: float = Field(default=0.4, ge=0.0, le=1.0)
    vo_ducking_db: float = Field(default=-6.0, description="How much to duck music during voiceover (in dB)")


# --- Action-to-SFX Mapping ---

ACTION_SFX_MAP = {
    # Physical actions
    "kick": [("whoosh", 0.0, "medium"), ("impact", 0.3, "heavy")],
    "punch": [("whoosh", 0.0, "subtle"), ("impact", 0.2, "heavy")],
    "spin": [("swoosh", 0.0, "medium")],
    "jump": [("whoosh", 0.0, "subtle"), ("impact", 0.5, "medium")],
    "slam": [("impact", 0.0, "heavy"), ("cinematic_boom", 0.1, "heavy")],
    "throw": [("whoosh", 0.0, "medium")],
    "catch": [("impact", 0.0, "subtle")],
    "open": [("click", 0.0, "subtle"), ("pop", 0.1, "medium")],
    "shatter": [("glass_shatter", 0.0, "heavy")],
    "unbox": [("pop", 0.0, "medium"), ("rise_tension", -0.5, "subtle")],
    # Digital/tech actions
    "type": [("typing_burst", 0.0, "subtle")],
    "typing": [("typing_burst", 0.0, "subtle")],
    "click": [("click", 0.0, "subtle")],
    "activate": [("power_up", 0.0, "medium"), ("digital_glitch", 0.1, "subtle")],
    "deactivate": [("power_down", 0.0, "medium")],
    "glitch": [("digital_glitch", 0.0, "medium")],
    "notification": [("notification_ding", 0.0, "subtle")],
    "load": [("rise_tension", 0.0, "subtle"), ("hit_resolve", 0.8, "medium")],
    "sync": [("power_up", 0.0, "subtle"), ("notification_ding", 0.3, "subtle")],
    # Camera/cinematic actions
    "reveal": [("reverse_cymbal", -0.5, "medium"), ("cinematic_boom", 0.0, "medium")],
    "emerge": [("rise_tension", -0.3, "medium"), ("hit_resolve", 0.0, "medium")],
    "levitate": [("ambient_drone", 0.0, "subtle"), ("rise_tension", 0.0, "subtle")],
    "hover": [("ambient_drone", 0.0, "subtle")],
    "explode": [("cinematic_boom", 0.0, "heavy"), ("explosion_soft", 0.1, "heavy")],
    "resolve": [("hit_resolve", 0.0, "medium")],
    "fade": [("tape_stop", 0.0, "subtle")],
    "burst": [("cinematic_boom", 0.0, "medium"), ("whoosh", 0.0, "medium")],
    "accelerate": [("rise_tension", 0.0, "medium"), ("whoosh", 0.5, "heavy")],
    "flash": [("cinematic_boom", 0.0, "subtle"), ("pop", 0.0, "subtle")],
    "flare": [("rise_tension", -0.3, "subtle"), ("cinematic_boom", 0.0, "medium")],
}

# Scene purpose -> ambient bed
AMBIENT_MAP = {
    "hook_problem": "low_tension_drone",
    "hook": "low_tension_drone",
    "problem": "low_tension_drone",
    "solution_reveal": "techy_ambient_pad",
    "solution": "techy_ambient_pad",
    "3d_title": "deep_space_ambient",
    "paradigm_shift": "deep_space_ambient",
    "ui_walkthrough": "soft_click_ambient",
    "feature": "soft_click_ambient",
    "cta": "uplifting_resolve_pad",
    "closing": "uplifting_resolve_pad",
    "end_card": "uplifting_resolve_pad",
}


class SFXBeatEngine:
    def __init__(self):
        pass

    def generate_sfx_plan(self, storyboard_scenes: list) -> AudioMixPlan:
        """
        Maps storyboard visual events to SFX cues.
        Derives SFX from core_action keywords rather than blindly inserting effects.
        """
        scene_plans = []

        for scene in storyboard_scenes:
            scene_id = scene.get("scene_id", "00")
            purpose = scene.get("purpose", "").lower()
            
            # Get core_action from visual_elements if available
            visual_elements = scene.get("visual_elements", {})
            core_action = visual_elements.get("core_action", "") if isinstance(visual_elements, dict) else ""
            
            # Derive SFX cues from action keywords
            sfx_cues = self._extract_sfx_from_action(core_action, scene.get("duration", 4.0))
            
            # Determine ambient bed from scene purpose
            ambient = AMBIENT_MAP.get(purpose, "neutral_room_tone")

            scene_plans.append(SceneSFXPlan(
                scene_id=scene_id,
                sfx_cues=sfx_cues,
                ambient_bed=ambient,
                ambient_volume=0.25 if purpose in ["cta", "closing"] else 0.35
            ))

        plan = AudioMixPlan(scenes=scene_plans)
        logger.info(f"[SFXBeatEngine] Generated audio plan for {len(scene_plans)} scenes with {sum(len(s.sfx_cues) for s in scene_plans)} total SFX cues.")
        return plan

    def _extract_sfx_from_action(self, core_action: str, scene_duration: float) -> List[SFXCue]:
        """
        Scans core_action text for known keywords and maps them to SFX events.
        Times the SFX relative to scene midpoint if no specific timing is given.
        """
        if not core_action:
            return []

        action_lower = core_action.lower()
        cues = []
        midpoint = scene_duration / 2.0

        for keyword, sfx_list in ACTION_SFX_MAP.items():
            if keyword in action_lower:
                for sfx_type, offset, intensity in sfx_list:
                    timestamp = max(0.0, midpoint + offset)
                    timestamp = min(timestamp, scene_duration - 0.2)
                    cues.append(SFXCue(
                        timestamp=round(timestamp, 2),
                        sfx_type=sfx_type,
                        intensity=intensity,
                        duration=0.5 if intensity != "heavy" else 0.8,
                        trigger_action=f"{keyword} -> {core_action[:60]}"
                    ))

        # Deduplicate by (sfx_type, timestamp) keeping first occurrence
        seen = set()
        unique_cues = []
        for cue in cues:
            key = (cue.sfx_type, cue.timestamp)
            if key not in seen:
                seen.add(key)
                unique_cues.append(cue)

        return unique_cues

    def save_audio_plan(self, plan: AudioMixPlan, output_path: Path) -> Path:
        """Saves the audio mix plan as JSON for downstream audio processing."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plan.model_dump_json(indent=2))
        logger.info(f"[SFXBeatEngine] Audio plan saved to {output_path}")
        return output_path


if __name__ == "__main__":
    # Test with mock storyboard scenes
    mock_scenes = [
        {
            "scene_id": "01",
            "purpose": "Hook_Problem",
            "duration": 4.5,
            "visual_elements": {
                "characters": ["Frustrated software engineer slumped at desk"],
                "key_items": ["Overheating dual monitors"],
                "core_action": "Engineer rubs temples as red server alerts pulse on screens",
                "visual_setting": "Dark moody server room"
            }
        },
        {
            "scene_id": "02",
            "purpose": "Solution_Reveal",
            "duration": 5.0,
            "visual_elements": {
                "characters": [],
                "key_items": ["Glowing crystalline microchip"],
                "core_action": "Microchip levitates and activates with intense violet energy beam",
                "visual_setting": "Futuristic studio with purple rim lighting"
            }
        },
        {
            "scene_id": "05",
            "purpose": "CTA",
            "duration": 3.5,
            "visual_elements": {
                "characters": [],
                "key_items": ["3D brand logo prism"],
                "core_action": "Logo prism resolves to camera center with dynamic light flare burst",
                "visual_setting": "Deep space background"
            }
        }
    ]

    engine = SFXBeatEngine()
    plan = engine.generate_sfx_plan(mock_scenes)
    print(plan.model_dump_json(indent=2))
    print(f"\n[PASS] Generated {sum(len(s.sfx_cues) for s in plan.scenes)} SFX cues across {len(plan.scenes)} scenes.")
