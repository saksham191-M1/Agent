from __future__ import annotations
import uuid
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class CameraMove(BaseModel):
    shot_type: Literal[
        "extreme_close_up", "close_up", "medium_close_up", 
        "medium", "medium_wide", "wide", "extreme_wide",
        "overhead", "low_angle", "dutch_angle"
    ] = "medium_wide"
    movement: Literal[
        "static", "push_in_slow", "push_in_fast", "pull_out",
        "tracking_dolly", "orbit_subtle", "orbit_full",
        "crane_up", "crane_down", "handheld_shake",
        "whip_pan", "tilt_up", "tilt_down"
    ] = "static"
    speed: Literal["real_time", "slow_motion", "timelapse", "ramped"] = "real_time"
    focus: str = Field(default="center subject", description="What/who the camera should focus on")


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: f"entity_{uuid.uuid4().hex[:6]}")
    type: Literal["character", "object", "environment_prop"] = "object"
    description: str
    persistent: bool = Field(default=True, description="Must this entity appear consistently across scenes?")


class VisualElements(BaseModel):
    characters: List[str] = Field(default_factory=list, description="Who is in frame")
    key_items: List[str] = Field(default_factory=list, description="Key props or hero objects")
    core_action: str = Field(description="Specific physical action happening")
    visual_setting: str = Field(description="Environment and atmosphere")
    camera_move: CameraMove = Field(default_factory=CameraMove)


class SceneConstraints(BaseModel):
    must_preserve: List[str] = Field(default_factory=list, description="Elements that must remain across shots")
    must_not_include: List[str] = Field(default_factory=list, description="Elements that must NOT appear")


class SceneContract(BaseModel):
    scene_id: str
    purpose: str
    duration: float = Field(ge=1.0, le=30.0)
    voiceover_line: str = Field(max_length=200)
    visual_elements: VisualElements
    constraints: SceneConstraints = Field(default_factory=SceneConstraints)
    entity_refs: List[str] = Field(default_factory=list, description="IDs of entities used in this scene")


class VisualContract(BaseModel):
    script_id: str
    total_duration: float = Field(ge=3.0, le=120.0)
    tts_script_with_breaks: str
    tts_tone: Literal["conversational", "authoritative", "energetic"] = "conversational"
    music_genre: str = "ambient_electronic_build"
    energy_curve: Literal["slow_build_to_fast", "constant_energetic", "calm_to_triumphant"] = "slow_build_to_fast"
    entities: List[Entity] = Field(default_factory=list, description="Global entity registry for cross-scene consistency")
    scenes: List[SceneContract]

    @model_validator(mode="after")
    def validate_duration_sum(self) -> VisualContract:
        scene_sum = sum(s.duration for s in self.scenes)
        if abs(scene_sum - self.total_duration) > 2.0:
            raise ValueError(f"Scene durations sum ({scene_sum}s) differs from total_duration ({self.total_duration}s) by more than 2s")
        return self

    @model_validator(mode="after")
    def validate_entity_refs(self) -> VisualContract:
        entity_ids = {e.id for e in self.entities}
        for scene in self.scenes:
            for ref in scene.entity_refs:
                if ref not in entity_ids:
                    raise ValueError(f"Scene {scene.scene_id} references unknown entity '{ref}'. Known: {entity_ids}")
        return self
