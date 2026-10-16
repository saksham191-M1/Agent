import json
import re
from pathlib import Path
from typing import List, Literal, Union

from pydantic import BaseModel, Field

# --- Pydantic Schemas ---

class Keyframe(BaseModel):
    time: float
    value: Union[float, List[float], str]
    easing: Literal["linear", "easeIn", "easeOut", "easeInOut"] = "easeInOut"

class Layer(BaseModel):
    id: str
    type: Literal["footage", "text", "camera", "adjustment", "solid"]
    name: str
    track: int
    startTime: float
    duration: float
    properties: dict = Field(default_factory=dict)
    keyframes: dict = Field(default_factory=dict)

class Ecproj(BaseModel):
    version: str = "1.0"
    composition: dict
    layers: List[Layer]

# --- Paths ---
TEMPLATE_DIR = Path("jarvis/ai_content/prompts/templates")
if not TEMPLATE_DIR.exists():
    TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "prompts" / "templates"

TEMP_DIR = Path("jarvis/ai_content/output/temp_ecproj")
if not TEMP_DIR.parent.exists():
    TEMP_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "temp_ecproj"

# Fallback colors if brand extraction fails
DEFAULTS = {
    "primary_color": "#7C3AED",
    "secondary_color": "#0A0A12",
    "title": "Your Title Here",
    "subtitle": "",
    "cta_text": "Get Started",
    "logo_path": "",
    "color_grade": "teal_orange_cinematic",
    "veo_clip_path": ""
}

TEMPLATE_MAP = {
    "title_card": "template_title_card.json",
    "video_overlay": "template_video_overlay.json",
    "3d_text": "template_3d_text.json",
    "cta_sting": "template_cta_sting.json"
}

def select_template(scene: dict) -> str:
    """Maps storyboard purpose to template file."""
    purpose = str(scene.get("purpose", "")).lower()
    
    if purpose in ["cta", "cta_sting", "closing", "end_card"]:
        return TEMPLATE_MAP["cta_sting"]
    if purpose in ["3d_title", "paradigm", "paradigm_shift"] or scene.get("needs_particles") is True:
        return TEMPLATE_MAP["3d_text"]
    if purpose in ["hook_problem", "title", "hook", "problem"]:
        return TEMPLATE_MAP["title_card"]
    # Default for feature, solution_reveal, workflow, ui
    return TEMPLATE_MAP["video_overlay"]

def _inject_vars(obj, variables: dict):
    """Recursively replaces {{var}} in strings inside dict/list."""
    if isinstance(obj, str):
        # Find all {{var}} and replace
        def replacer(match):
            key = match.group(1).strip()
            return str(variables.get(key, match.group(0)))
        return re.sub(r"\{\{(.*?)\}\}", replacer, obj)
    
    if isinstance(obj, dict):
        return {k: _inject_vars(v, variables) for k, v in obj.items()}
    
    if isinstance(obj, list):
        return [_inject_vars(item, variables) for item in obj]
    
    return obj

def load_template(template_filename: str, variables: dict) -> dict:
    """Loads JSON template and injects variables."""
    path = TEMPLATE_DIR / template_filename
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}. Did you split effectcraft_templates.md into 4 json files?")
    
    data = json.loads(path.read_text())
    return _inject_vars(data, variables)

def build_ecproj(scene: dict, veo_clip: Union[str, Path]) -> Ecproj:
    """
    Main builder: scene_data + veo_clip -> validated Ecproj object
    scene must contain: scene_id, duration, title, purpose
    """
    veo_path = Path(veo_clip).as_posix() if isinstance(veo_clip, Path) else str(veo_clip).replace("\\", "/")
    duration = float(scene.get("duration", 4.5))
    
    # Prepare variables for injection
    variables = {**DEFAULTS}
    variables.update({
        "title": scene.get("title", DEFAULTS["title"]),
        "subtitle": scene.get("subtitle", DEFAULTS["subtitle"]),
        "primary_color": scene.get("primary_color", DEFAULTS["primary_color"]),
        "secondary_color": scene.get("secondary_color", DEFAULTS["secondary_color"]),
        "color_grade": scene.get("color_grade", DEFAULTS["color_grade"]),
        "cta_text": scene.get("cta_text", DEFAULTS["cta_text"]),
        "logo_path": scene.get("logo_path", DEFAULTS["logo_path"]),
        "veo_clip_path": veo_path,
    })
    # Allow scene to override any var
    for k, v in scene.items():
        if isinstance(v, (str, int, float)):
            variables[k] = v

    template_file = select_template(scene)
    raw_data = load_template(template_file, variables)

    # Override composition duration to match scene duration
    raw_data["composition"]["duration"] = duration
    
    # Fix all layer durations that were hardcoded to old template duration
    for layer in raw_data["layers"]:
        if layer["type"] != "camera": # Keep camera full duration
            # Clamp layer duration to scene duration
            layer["duration"] = min(float(layer["duration"]), duration)
            layer["startTime"] = min(float(layer["startTime"]), duration - 0.1)
        else:
            layer["duration"] = duration

    # Validate with Pydantic
    ecproj = Ecproj.model_validate(raw_data)
    return ecproj

def save_ecproj(ecproj: Ecproj, scene_id: str) -> Path:
    """Saves to output/temp_ecproj/scene_{id}.ecproj"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TEMP_DIR / f"scene_{scene_id}.ecproj"
    out_path.write_text(ecproj.model_dump_json(indent=2))
    return out_path

# --- Test Block ---
if __name__ == "__main__":
    # Mock test without needing any API keys
    mock_scene = {
        "scene_id": "01",
        "duration": 4.5,
        "purpose": "Hook_Problem",
        "title": "Tired of Chaos?",
        "subtitle": "Meet LinearApp",
        "primary_color": "#0EA5E9",
        "secondary_color": "#020617",
        "color_grade": "cold_dev_dark",
        "needs_particles": False
    }
    
    try:
        proj = build_ecproj(mock_scene, Path("jarvis/ai_content/output/renders/raw/scene_01_raw.mp4"))
        saved = save_ecproj(proj, mock_scene["scene_id"])
        print(f"[OK] Built {saved}")
        print(f"Composition: {proj.composition}")
        print(f"Layers: {[l.name for l in proj.layers]}")
        # Validation check
        assert len(proj.layers) == 4, "Must have 4 layers"
        print("[PASS] Ecproj.model_validate passed")
    except Exception as e:
        print(f"[FAIL] {e}")
        raise
