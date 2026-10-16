import logging
from typing import Tuple
from pydantic import ValidationError
from jarvis.ai_content.scripts.models.visual_contract import VisualContract, SceneContract
from jarvis.ai_content.scripts.models.storyboard_contract import ValidatedStoryboard, StoryboardShot

logger = logging.getLogger(__name__)


class ValidationResult:
    def __init__(self, valid: bool, data=None, errors: list = None, warnings: list = None):
        self.valid = valid
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self):
        return self.valid


def validate_visual_contract(raw_script: dict) -> ValidationResult:
    """
    Validation Gate 1: Validates Content Planner output before it reaches Storyboard Generator.
    Hard failures: missing fields, invalid types, impossible durations, unknown entity IDs.
    Soft failures: weak composition choices (logged as warnings).
    """
    errors = []
    warnings = []

    # Normalize: accept both flat scenes_outline and structured scenes
    if "scenes_outline" in raw_script and "scenes" not in raw_script:
        raw_script["scenes"] = raw_script.pop("scenes_outline")

    try:
        contract = VisualContract.model_validate(raw_script)
    except ValidationError as e:
        for err in e.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            errors.append(f"[HARD] {field}: {err['msg']}")
        return ValidationResult(valid=False, errors=errors)

    # Soft checks
    for scene in contract.scenes:
        if len(scene.visual_elements.characters) == 0 and len(scene.visual_elements.key_items) == 0:
            warnings.append(f"Scene {scene.scene_id}: No characters or key_items defined. Visual may be abstract.")
        if len(scene.voiceover_line) < 5:
            warnings.append(f"Scene {scene.scene_id}: Very short voiceover line ({len(scene.voiceover_line)} chars).")
        if not scene.visual_elements.core_action:
            errors.append(f"[HARD] Scene {scene.scene_id}: core_action is empty.")

    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    for w in warnings:
        logger.warning(w)

    return ValidationResult(valid=True, data=contract, warnings=warnings)


def validate_storyboard(raw_storyboard: dict, contract: VisualContract) -> ValidationResult:
    """
    Validation Gate 2: Validates Storyboard Generator output before video generation.
    Checks entity references, timing consistency, and visual preservation constraints.
    """
    errors = []
    warnings = []

    try:
        storyboard = ValidatedStoryboard.model_validate(raw_storyboard)
    except ValidationError as e:
        for err in e.errors():
            field = " -> ".join(str(loc) for loc in err["loc"])
            errors.append(f"[HARD] {field}: {err['msg']}")
        return ValidationResult(valid=False, errors=errors)

    # Cross-reference: every contract scene should have a matching storyboard shot
    contract_ids = {s.scene_id for s in contract.scenes}
    storyboard_ids = {s.scene_id for s in storyboard.storyboard}
    missing = contract_ids - storyboard_ids
    if missing:
        errors.append(f"[HARD] Missing storyboard shots for scenes: {missing}")

    # Check duration alignment
    for shot in storyboard.storyboard:
        matching_scene = next((s for s in contract.scenes if s.scene_id == shot.scene_id), None)
        if matching_scene and abs(shot.duration - matching_scene.duration) > 1.0:
            warnings.append(
                f"Scene {shot.scene_id}: Storyboard duration ({shot.duration}s) "
                f"differs from contract ({matching_scene.duration}s) by > 1s."
            )

    # Check veo_prompt is not empty
    for shot in storyboard.storyboard:
        if len(shot.veo_prompt.strip()) < 20:
            errors.append(f"[HARD] Scene {shot.scene_id}: veo_prompt is too short ({len(shot.veo_prompt)} chars).")

    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    for w in warnings:
        logger.warning(w)

    return ValidationResult(valid=True, data=storyboard, warnings=warnings)


def validate_generated_clip(
    clip_path,
    expected_duration: float,
    expected_aspect: str = "16:9",
    scene_id: str = "00"
) -> ValidationResult:
    """
    Validation Gate 3: Post-Generation Quality Check.
    Verifies clip exists, is non-empty, and checks video stream metadata via ffprobe when available.
    """
    import json
    import subprocess
    from pathlib import Path

    path = Path(clip_path)
    errors = []
    warnings = []

    if not path.exists():
        errors.append(f"[HARD] Scene {scene_id}: Generated clip does not exist at {path}")
        return ValidationResult(valid=False, errors=errors)

    size = path.stat().st_size
    if size < 512:
        errors.append(f"[HARD] Scene {scene_id}: Generated clip is corrupt or empty ({size} bytes)")
        return ValidationResult(valid=False, errors=errors)

    # Probe video metadata via ffprobe if available
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration",
            "-of", "json",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(res.stdout)
        streams = probe_data.get("streams", [])
        if streams:
            stream = streams[0]
            width = int(stream.get("width", 0))
            height = int(stream.get("height", 0))
            duration = float(stream.get("duration", expected_duration))

            if abs(duration - expected_duration) > 1.5:
                warnings.append(
                    f"Scene {scene_id}: Clip duration ({duration:.1f}s) differs from requested ({expected_duration:.1f}s)"
                )

            if expected_aspect == "16:9" and height > 0:
                ratio = width / height
                if abs(ratio - (16 / 9)) > 0.1:
                    warnings.append(f"Scene {scene_id}: Aspect ratio {width}x{height} ({ratio:.2f}) differs from 16:9")
    except Exception:
        # ffprobe not installed or placeholder binary clip
        pass

    for w in warnings:
        logger.warning(w)

    return ValidationResult(valid=True, data=path, warnings=warnings)

