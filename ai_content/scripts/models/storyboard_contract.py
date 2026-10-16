from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class StoryboardShot(BaseModel):
    scene_id: str
    duration: float = Field(ge=1.0, le=30.0)
    purpose: str
    veo_prompt: str = Field(max_length=300, description="Veo 3.1 visual prompt grounded in visual_elements")
    title: str = Field(default="", max_length=40)
    subtitle: str = Field(default="", max_length=80)
    compositor_tag: Literal["vfx_effectcraft", "motion_remotion"] = "vfx_effectcraft"
    color_grade: str = "teal_orange_cinematic"
    camera_move: str = "push_in_slow"
    needs_particles: bool = False
    text_animation: str = "kinetic_scale_blur"
    entity_refs: List[str] = Field(default_factory=list)
    must_preserve: List[str] = Field(default_factory=list)
    must_not_include: List[str] = Field(default_factory=list)


class ValidatedStoryboard(BaseModel):
    storyboard: List[StoryboardShot]

    @model_validator(mode="after")
    def validate_effectcraft_ratio(self) -> ValidatedStoryboard:
        total = len(self.storyboard)
        if total == 0:
            raise ValueError("Storyboard must have at least 1 shot")
        vfx_count = sum(1 for s in self.storyboard if s.compositor_tag == "vfx_effectcraft")
        ratio = vfx_count / total
        # Warn but don't hard-fail for now
        if ratio < 0.5:
            import logging
            logging.getLogger(__name__).warning(f"Only {ratio:.0%} of scenes use vfx_effectcraft (recommended >= 60%)")
        return self
