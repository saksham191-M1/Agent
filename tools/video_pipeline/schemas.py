"""
schemas.py
──────────
Pydantic schemas for the Director AI Gateway.
Defines strict contracts for ProductProfile, Storyboard, Critique, and test schemas.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ──────────────────────────────────────────────────────────────────────────────
# Test / Toy Schema for Unit Testing & Mock Verification
# ──────────────────────────────────────────────────────────────────────────────

class ToyTestSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")
    headline: str = Field(..., description="Short punchy headline without terminal punctuation")
    rating: float = Field(..., ge=0.0, le=5.0, description="Numerical rating between 0 and 5")
    tags: List[str] = Field(default_factory=list, description="Categorical tags")
    is_valid: bool = Field(default=True)


# ──────────────────────────────────────────────────────────────────────────────
# Phase 3: Product Profile Schema
# ──────────────────────────────────────────────────────────────────────────────

class ToneEnum(str, Enum):
    playful = "playful"
    premium = "premium"
    technical = "technical"
    urgent = "urgent"
    warm = "warm"
    bold = "bold"
    minimal = "minimal"


class ProofPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    text: str = Field(..., description="Fact or statistic extracted from crawl")
    source: str = Field(..., description="Page section, element, or URL source of fact")


class ProductProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(..., description="Clean brand/product name")
    what_it_is: str = Field(..., description="One sentence in plain language explaining what the product does")
    audience: str = Field(..., description="Target audience or user segment")
    core_differentiator: str = Field(..., description="The single sharpest reason to choose it")
    tone: ToneEnum = Field(..., description="Creative tone for copy, motion, and music")
    category: str = Field(..., description="Free text category descriptor, e.g. ecommerce, b2b saas, dev tool")
    visual_style_hint: str = Field(..., description="E.g. dark and dense, bright and friendly, minimal luxury")
    proof_points: List[ProofPoint] = Field(default_factory=list, description="Extracted factual proof points")
    visual_assets_available: List[str] = Field(default_factory=list, description="Filenames that actually exist")
    missing_data: List[str] = Field(default_factory=list, description="Data absent from crawl, e.g. price, rating")
    language: str = Field(default="en", description="Primary language of the product & ad copy")


# ──────────────────────────────────────────────────────────────────────────────
# Phase 4: Narrative Arc Schema
# ──────────────────────────────────────────────────────────────────────────────

class SceneBlueprint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str = Field(..., description="hook | problem | feature | demo | proof | cta | pricing")
    target_duration: float = Field(..., ge=1.5, le=10.0)
    allowed_layouts: List[str] = Field(default_factory=list)
    allowed_motion: List[str] = Field(default_factory=list)
    vo_instruction: str = Field(...)


class NarrativeArc(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    suitable_tones: List[ToneEnum]
    suitable_categories: List[str]
    scene_count_range: List[int] = Field(..., description="[min_scenes, max_scenes]")
    duration_seconds_range: List[float] = Field(..., description="[min_sec, max_sec]")
    scene_blueprints: List[SceneBlueprint]


# ──────────────────────────────────────────────────────────────────────────────
# Phase 5: Storyboard Schema
# ──────────────────────────────────────────────────────────────────────────────

class SceneDirectorSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")
    scene_id: int
    duration_seconds: float = Field(..., ge=1.5, le=10.0)
    layout: str = Field(..., description="hero-type | phone | split | browser | big-number | cta")
    motion_profile: str = Field(default="smooth", description="playful | premium | technical | aggressive | minimal")
    voiceover: str = Field(..., description="Spoken voice line for this scene")
    kinetic_text: str = Field(..., description="1-4 bold on-screen headline words WITHOUT terminal punctuation")
    visual_fx: str = Field(default="carousel_glide")
    transition_out: str = Field(default="carousel_glide")
    requires_ui_image: bool = Field(default=False)


class StoryboardDirectorSpec(BaseModel):
    model_config = ConfigDict(extra="ignore")
    product_name: str
    narrative_type: str
    scene_count: int = Field(..., ge=3, le=8)
    total_seconds: float = Field(..., ge=10.0, le=40.0)
    music_mood: str
    voice_style: str
    scenes: List[SceneDirectorSpec]


# ──────────────────────────────────────────────────────────────────────────────
# Phase 5: Critique Schema
# ──────────────────────────────────────────────────────────────────────────────

class CritiqueFeedback(BaseModel):
    model_config = ConfigDict(extra="ignore")
    passes_qa: bool
    invented_facts_detected: List[str] = Field(default_factory=list)
    punctuation_violations: List[str] = Field(default_factory=list)
    revision_notes: Optional[str] = None
    revised_storyboard: Optional[StoryboardDirectorSpec] = None
