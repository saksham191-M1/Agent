import os
import sys
import json
import logging
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from jarvis.ai_content.scripts.config import FINAL_RENDERS_DIR, OUTPUT_DIR
from jarvis.ai_content.scripts.providers.gemini_provider import GeminiProvider
from jarvis.ai_content.scripts.video.google_flow_automation import GoogleFlowAutomation
from jarvis.ai_content.scripts.compositors.effectcraft_engine import EffectCraftEngine
from jarvis.ai_content.scripts.audio.audio_mixer import AudioMixer
from jarvis.ai_content.scripts.audio.sfx_beat_engine import SFXBeatEngine
from jarvis.ai_content.scripts.pipeline import MasterAssembly
from jarvis.ai_content.scripts.models.visual_contract import VisualContract

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_live_demo():
    logger.info("=" * 60)
    logger.info("STARTING LIVE GOOGLE FLOW VEO 3.1 DEMO GENERATION")
    logger.info("=" * 60)

    # 1. Video Provider in LIVE MODE (mock_mode=False)
    video = GoogleFlowAutomation(mock_mode=False, headless=True)

    # 2. Hero Scene Spec
    scene = {
        "scene_id": "demo_01",
        "duration": 10.0,
        "purpose": "Solution_Reveal",
        "veo_prompt": "Cinematic 3D slow-motion close-up of a glowing crystalline microchip levitating with violet holographic circuits, dark studio, volumetric purple rim lighting, 16:9 photorealistic 8k",
        "title": "Pure Velocity",
        "subtitle": "Next-Gen Engineering Platform",
        "compositor_tag": "vfx_effectcraft",
        "primary_color": "#6366F1",
        "secondary_color": "#0A0A12",
        "color_grade": "teal_orange_cinematic",
        "needs_particles": True,
        "text_animation": "kinetic_scale_blur"
    }

    # Step A: Live Veo Generation via Google Flow
    logger.info(f"\n[DEMO] Triggering Live Veo Generation on Google Flow...")
    logger.info(f"[DEMO] Prompt: {scene['veo_prompt']}")
    raw_clip = video.generate_clip(
        prompt=scene["veo_prompt"],
        scene_id=scene["scene_id"],
        duration=int(scene["duration"]),
        aspect_ratio="16:9",
        model_tier="quality"
    )
    logger.info(f"[DEMO] Raw clip ready: {raw_clip} (size={raw_clip.stat().st_size} bytes)")

    # Step B: EffectCraft Compositing
    logger.info("\n[DEMO] Applying EffectCraft 3D kinetic title & particles...")
    effectcraft = EffectCraftEngine()
    composited_clip = effectcraft.render(scene, raw_clip)
    logger.info(f"[DEMO] Composited clip: {composited_clip}")

    # Step C: SFX Beat Engine & Audio Soundtrack
    logger.info("\n[DEMO] Generating synchronized soundtrack & SFX...")
    sfx_engine = SFXBeatEngine()
    audio_mixer = AudioMixer()

    enriched_scene = {
        **scene,
        "visual_elements": {
            "characters": [],
            "key_items": ["glowing crystalline microchip"],
            "core_action": "Microchip levitates and activates with intense violet energy beam burst",
            "visual_setting": "Futuristic clean dark studio with purple rim lighting"
        }
    }
    audio_plan = sfx_engine.generate_sfx_plan([enriched_scene])
    
    mock_contract = VisualContract(
        script_id="demo_01",
        total_duration=10.0,
        tts_script_with_breaks="Meet the next evolution of developer speed. Powered by pure intelligence.",
        tts_tone="authoritative",
        music_genre="ambient_electronic_build",
        energy_curve="slow_build_to_fast",
        entities=[],
        scenes=[{
            "scene_id": "demo_01",
            "purpose": "Solution_Reveal",
            "duration": 10.0,
            "voiceover_line": "Meet the next evolution of developer speed. Powered by pure intelligence.",
            "visual_elements": enriched_scene["visual_elements"],
            "entity_refs": []
        }]
    )
    master_audio = audio_mixer.mix(mock_contract, audio_plan)

    # Step D: Final Mux
    logger.info("\n[DEMO] Final Muxing into live_demo_ad.mp4...")
    output_ad_path = FINAL_RENDERS_DIR / "live_demo_ad.mp4"
    final_ad = MasterAssembly.concat([composited_clip], output_ad_path, master_audio_path=master_audio)

    logger.info("=" * 60)
    logger.info(f"DEMO READY: {final_ad}")
    logger.info("=" * 60)
    return final_ad


if __name__ == "__main__":
    run_live_demo()
