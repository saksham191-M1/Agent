import os
import sys
import json
import argparse
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from jarvis.ai_content.scripts.config import (
    PROMPTS_DIR, 
    FINAL_RENDERS_DIR, 
    BASE_DIR,
    OUTPUT_DIR
)
from jarvis.ai_content.scripts.providers.llm_provider import LLMProvider
from jarvis.ai_content.scripts.providers.gemini_provider import GeminiProvider
from jarvis.ai_content.scripts.video.base_video import VideoProvider
from jarvis.ai_content.scripts.video.google_flow_automation import GoogleFlowAutomation
from jarvis.ai_content.scripts.compositors.effectcraft_engine import EffectCraftEngine
from jarvis.ai_content.scripts.compositors.remotion_engine import RemotionEngine
from jarvis.ai_content.scripts.validators.contract_validator import (
    validate_visual_contract, validate_storyboard, validate_generated_clip
)
from jarvis.ai_content.scripts.audio.sfx_beat_engine import SFXBeatEngine
from jarvis.ai_content.scripts.audio.audio_mixer import AudioMixer
from jarvis.ai_content.scripts.metrics.tracker import RunTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# --- Load Prompts from system_prompts.md ---
def load_system_prompts():
    prompts_path = PROMPTS_DIR / "system_prompts.md"
    content = prompts_path.read_text(encoding="utf-8")
    
    director_prompt = "You are the Creative Director. Output pure JSON matching schema."
    planner_prompt = "You are the Content Planner. Output pure JSON matching schema."
    storyboard_prompt = "You are the Storyboard Generator. Output pure JSON matching schema."

    try:
        sections = content.split("## ")
        for sec in sections:
            sec_lower = sec.lower()
            if "creative director" in sec_lower:
                director_prompt = sec
            elif "content planner" in sec_lower:
                planner_prompt = sec
            elif "storyboard generator" in sec_lower:
                storyboard_prompt = sec
    except Exception as e:
        logger.warning(f"Failed to split prompts cleanly: {e}. Using extracted blocks.")

    return director_prompt, planner_prompt, storyboard_prompt

DIRECTOR_PROMPT, PLANNER_PROMPT, STORYBOARD_PROMPT = load_system_prompts()


class MasterAssembly:
    @staticmethod
    def concat(clip_paths: List[Path], output_path: Path, master_audio_path: Optional[Path] = None) -> Path:
        """
        Concatenates rendered scene clips and muxes synchronized master soundtrack.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        concat_file = output_path.parent / "concat_list.txt"
        
        # Write list of input clips (using forward slashes for ffmpeg safety)
        with open(concat_file, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{p.resolve().as_posix()}'\n")

        logger.info(f"[MasterAssembly] Concatenating {len(clip_paths)} clips...")
        temp_video = output_path.parent / "temp_concat_video.mp4"
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(temp_video)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            # If master audio track is provided, mux with video
            if master_audio_path and master_audio_path.exists() and master_audio_path.stat().st_size > 512:
                logger.info(f"[MasterAssembly] Muxing master audio soundtrack into {output_path}...")
                mux_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(temp_video),
                    "-i", str(master_audio_path),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-shortest",
                    str(output_path)
                ]
                subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if temp_video.exists():
                    temp_video.unlink(missing_ok=True)
            else:
                if temp_video.exists():
                    if output_path.exists():
                        output_path.unlink()
                    temp_video.rename(output_path)

            logger.info(f"[MasterAssembly] Final ad successfully generated: {output_path}")
            return output_path
        except Exception as e:
            logger.warning(f"[MasterAssembly] ffmpeg concat failed: {e}. Copying first clip as fallback.")
            if clip_paths and clip_paths[0].exists():
                output_path.write_bytes(clip_paths[0].read_bytes())
            return output_path


def run_pipeline(
    brief: dict, 
    llm: LLMProvider, 
    video: VideoProvider,
    output_ad_path: Path = FINAL_RENDERS_DIR / "final_ad.mp4"
) -> Path:
    logger.info("=" * 60)
    logger.info("STARTING AI CONTENT AD GENERATION PIPELINE")
    logger.info("=" * 60)

    tracker = RunTracker()

    # ────────────────────────────────────────────────────────
    # Stage 1: Creative Direction
    # ────────────────────────────────────────────────────────
    tracker.start_stage("Stage 1: Creative Direction")
    logger.info("[Pipeline] Stage 1: Creative Director generating style...")
    direction = llm.generate_json(DIRECTOR_PROMPT, json.dumps(brief))
    logger.info(f"[Pipeline] Direction selected: Tone={direction.get('tone')} Strategy={direction.get('compositor_strategy')}")
    tracker.end_stage()

    # ────────────────────────────────────────────────────────
    # Stage 2: Content Planning (Script + Visual Elements)
    # ────────────────────────────────────────────────────────
    tracker.start_stage("Stage 2: Content Planning")
    logger.info("[Pipeline] Stage 2: Content Planner drafting script with visual elements...")
    planner_payload = {"brief": brief, "creative_direction": direction}
    script = llm.generate_json(PLANNER_PROMPT, json.dumps(planner_payload))
    logger.info(f"[Pipeline] Script outline created with {len(script.get('scenes_outline', script.get('scenes', [])))} scenes.")

    # VALIDATION GATE 1: Visual Contract Validator
    logger.info("[Pipeline] ── Validation Gate 1: Checking Visual Contract ──")
    contract_result = validate_visual_contract(script)
    if not contract_result:
        for err in contract_result.errors:
            logger.error(f"  {err}")
        raise ValueError(f"Visual Contract validation failed with {len(contract_result.errors)} error(s). Fix planner output.")
    for warn in contract_result.warnings:
        logger.warning(f"  {warn}")
    contract = contract_result.data
    logger.info(f"[Pipeline] ✓ Visual Contract validated: {len(contract.scenes)} scenes, {len(contract.entities)} entities registered.")
    tracker.end_stage()

    # ────────────────────────────────────────────────────────
    # Stage 3: Storyboarding & Routing
    # ────────────────────────────────────────────────────────
    tracker.start_stage("Stage 3: Storyboarding")
    logger.info("[Pipeline] Stage 3: Storyboard Generator creating Veo prompts & routing...")
    storyboard_payload = {"script": script, "creative_direction": direction}
    storyboard_resp = llm.generate_json(STORYBOARD_PROMPT, json.dumps(storyboard_payload))

    # VALIDATION GATE 2: Storyboard Validator
    logger.info("[Pipeline] ── Validation Gate 2: Checking Storyboard ──")
    storyboard_result = validate_storyboard(storyboard_resp, contract)
    if not storyboard_result:
        for err in storyboard_result.errors:
            logger.error(f"  {err}")
        raise ValueError(f"Storyboard validation failed with {len(storyboard_result.errors)} error(s). Fix storyboard output.")
    for warn in storyboard_result.warnings:
        logger.warning(f"  {warn}")
    validated_storyboard = storyboard_result.data
    scenes = [shot.model_dump() for shot in validated_storyboard.storyboard]
    logger.info(f"[Pipeline] ✓ Storyboard validated: {len(scenes)} shots ready for generation.")
    tracker.end_stage()

    # ────────────────────────────────────────────────────────
    # Stage 4: SFX Beat Engine & Multi-Track Audio Mixer
    # ────────────────────────────────────────────────────────
    tracker.start_stage("Stage 4: Audio Mix & SFX Engine")
    logger.info("[Pipeline] Stage 4: SFX Beat Engine mapping visual events to audio cues...")
    sfx_engine = SFXBeatEngine()
    enriched_scenes_for_sfx = []
    for shot in scenes:
        matching_contract_scene = next(
            (s for s in contract.scenes if s.scene_id == shot["scene_id"]), None
        )
        if matching_contract_scene:
            shot["visual_elements"] = matching_contract_scene.visual_elements.model_dump()
        enriched_scenes_for_sfx.append(shot)
    
    audio_plan = sfx_engine.generate_sfx_plan(enriched_scenes_for_sfx)
    sfx_output = OUTPUT_DIR / "audio_mix_plan.json"
    sfx_engine.save_audio_plan(audio_plan, sfx_output)
    total_cues = sum(len(s.sfx_cues) for s in audio_plan.scenes)
    logger.info(f"[Pipeline] ✓ Audio plan generated: {total_cues} SFX cues across {len(audio_plan.scenes)} scenes.")

    # Mix audio tracks into master soundtrack
    audio_mixer = AudioMixer()
    master_audio = audio_mixer.mix(contract, audio_plan)
    tracker.end_stage()

    # ────────────────────────────────────────────────────────
    # Stage 5: Video Generation & Compositing Loop
    # ────────────────────────────────────────────────────────
    tracker.start_stage("Stage 5: Video Generation & Compositing")
    effectcraft = EffectCraftEngine()
    remotion = RemotionEngine()
    final_clips: List[Path] = []

    for idx, scene in enumerate(scenes, 1):
        scene_id = scene.get("scene_id", f"{idx:02d}")
        duration = int(float(scene.get("duration", 5.0)))
        veo_prompt = scene.get("veo_prompt", "Cinematic product visual")
        compositor_tag = scene.get("compositor_tag", "vfx_effectcraft")

        logger.info(f"\n--- Processing Scene {scene_id} ({compositor_tag}) ---")
        logger.info(f"Veo Prompt: {veo_prompt}")

        # Inject brand palette into scene data for EffectCraft templating
        scene["primary_color"] = direction.get("palette", {}).get("primary", "#6366F1")
        scene["secondary_color"] = direction.get("palette", {}).get("secondary", "#0A0A12")

        # Step A: Generate raw clip
        raw_clip = video.generate_clip(
            prompt=veo_prompt,
            scene_id=scene_id,
            duration=duration,
            aspect_ratio="16:9",
            model_tier="quality"
        )
        logger.info(f"Raw clip generated: {raw_clip}")

        # Validation Gate 3: Post-Generation Quality Check
        clip_check = validate_generated_clip(raw_clip, expected_duration=float(duration), scene_id=scene_id)
        if not clip_check:
            for err in clip_check.errors:
                logger.error(f"  {err}")
            raise ValueError(f"Generated clip for scene {scene_id} failed post-generation quality check.")
        logger.info(f"[Pipeline] ✓ Gate 3 passed for Scene {scene_id} raw clip.")

        # Step B: Route to appropriate compositor
        if compositor_tag == "vfx_effectcraft":
            rendered_clip = effectcraft.render(scene, raw_clip)
        else:
            rendered_clip = remotion.render(scene, raw_clip)

        logger.info(f"Composited clip ready: {rendered_clip}")
        final_clips.append(rendered_clip)

        tracker.record_scene_generation(
            scene_id=scene_id,
            compositor_tag=compositor_tag,
            duration=duration,
            model_tier="quality",
            retries=0,
            success=True
        )
    tracker.end_stage()

    # ────────────────────────────────────────────────────────
    # Stage 6: Master Assembly
    # ────────────────────────────────────────────────────────
    tracker.start_stage("Stage 6: Master Assembly")
    logger.info("\n[Pipeline] Stage 6: Master Assembly & Final Concat...")
    final_ad = MasterAssembly.concat(final_clips, output_ad_path, master_audio_path=master_audio)
    tracker.end_stage()

    metrics = tracker.export_summary()
    logger.info("=" * 60)
    logger.info(f"PIPELINE COMPLETE: {final_ad}")
    logger.info(f"Credits Remaining: {metrics['google_flow_credits']['credits_remaining']} / {metrics['google_flow_credits']['initial_credits']}")
    logger.info("=" * 60)
    return final_ad


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Content Pipeline Orchestrator")
    parser.add_argument("--brief", type=str, default=str(BASE_DIR / "input" / "test_brief.json"), help="Path to input brief JSON")
    parser.add_argument("--mock", action="store_true", help="Run with mock providers without calling live APIs or browsers")
    parser.add_argument("--output", type=str, default=str(FINAL_RENDERS_DIR / "final_ad.mp4"), help="Output path for final ad MP4")

    args = parser.parse_args()

    # Load Brief
    brief_path = Path(args.brief)
    if not brief_path.exists():
        logger.warning(f"Brief file {brief_path} not found. Using default internal brief.")
        brief_data = {
            "product": "LinearFlow",
            "description": "High-velocity issue tracking for dev teams",
            "target_audience": "developers"
        }
    else:
        brief_data = json.loads(brief_path.read_text(encoding="utf-8"))

    # Select Providers
    llm_provider = GeminiProvider() # Falls back to mock automatically if no API key
    video_provider = GoogleFlowAutomation(mock_mode=args.mock)

    run_pipeline(
        brief=brief_data,
        llm=llm_provider,
        video=video_provider,
        output_ad_path=Path(args.output)
    )
