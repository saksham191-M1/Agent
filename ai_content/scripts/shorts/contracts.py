from __future__ import annotations
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class ContentStyle(str, Enum):
    PRODUCT_AD = "product_ad"
    COMEDY_SKETCH = "comedy_sketch"
    CURIOSITY_LIFEHACK = "curiosity_lifehack"
    RELATABLE_POV = "relatable_pov"


class HookArchetype(str, Enum):
    PATTERN_INTERRUPT = "pattern_interrupt"
    CONTRARIAN = "contrarian"
    CURIOSITY_GAP = "curiosity_gap"
    RELATABLE_PAIN = "relatable_pain"
    ABSURD_COMEDY = "absurd_comedy"
    SECRET_LEAK = "secret_leak"


class ShortScene(BaseModel):
    scene_id: str
    purpose: Literal["hook", "escalation", "climax", "loop_cta"]
    duration: float = Field(ge=1.5, le=7.0, description="Scene duration in seconds")
    spoken_line: str = Field(description="Spoken narration or character dialogue")
    kinetic_text: str = Field(max_length=50, description="Punchy on-screen caption (3-6 words)")
    visual_prompt: str = Field(description="Prompt for Veo / Google Flow or B-roll description")
    visual_asset_source: Literal["google_flow_veo", "reusable_vault"] = "google_flow_veo"
    sfx_cue: str = Field(
        default="whoosh",
        description="Sound effect trigger (whoosh, vine_boom, cinematic_boom, record_scratch, pop, glitch)"
    )
    camera_velocity: Literal["explosive_push", "whip_pan", "subtle_orbit", "static", "handheld_shake"] = "explosive_push"

    @model_validator(mode="after")
    def validate_spoken_word_count(self) -> ShortScene:
        # In spoken English for short-form video, cadence is ~2.5 - 3.2 words per second
        words = len(self.spoken_line.split())
        max_allowed_words = int(self.duration * 3.5) + 3
        if words > max_allowed_words:
            raise ValueError(
                f"Scene '{self.scene_id}' has {words} words for {self.duration}s. "
                f"Maximum recommended is {max_allowed_words} words to prevent rushed audio."
            )
        return self


class ShortsScriptContract(BaseModel):
    title: str = Field(max_length=80)
    topic: str
    style: ContentStyle
    hook_archetype: HookArchetype
    total_duration: float = Field(ge=10.0, le=15.0, description="Strict 10-15s short-form duration")
    aspect_ratio: str = Field(default="9:16", description="Vertical 1080x1920 mobile format")
    music_vibe: str = Field(default="energetic_phonk_beat", description="Background music bed style")
    scenes: List[ShortScene] = Field(min_length=3, max_length=5)
    retention_score: float = Field(default=85.0, ge=0.0, le=100.0)
    loop_seamless: bool = Field(default=True, description="Does the final sentence naturally loop into the hook?")

    @model_validator(mode="after")
    def validate_duration_sum(self) -> ShortsScriptContract:
        scene_sum = sum(s.duration for s in self.scenes)
        if abs(scene_sum - self.total_duration) > 0.8:
            raise ValueError(
                f"Scene durations sum ({scene_sum:.2f}s) differs from total_duration ({self.total_duration:.2f}s) by > 0.8s"
            )
        return self

    @model_validator(mode="after")
    def validate_hook_scene(self) -> ShortsScriptContract:
        if not self.scenes or self.scenes[0].purpose != "hook":
            raise ValueError("Scene 0 must have purpose='hook' for algorithmic retention.")
        if self.scenes[0].duration > 3.0:
            raise ValueError(f"Hook duration ({self.scenes[0].duration}s) exceeds 3.0s limit for short-form video.")
        return self
