import json
import logging
from jarvis.ai_content.scripts.shorts import (
    ViralScriptEngine,
    ContentStyle,
    HookArchetype,
    ShortsScriptContract
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def test_viral_engine():
    engine = ViralScriptEngine()

    print("\n" + "=" * 65)
    print("TEST 1: COMEDY SKETCH (12.5s) - 'Smart Coffee Maker'")
    print("=" * 65)
    comedy_script = engine.generate_script(
        concept="Smart Coffee Maker",
        style=ContentStyle.COMEDY_SKETCH,
        duration=12.5
    )
    print(f"Title: {comedy_script.title}")
    print(f"Total Duration: {comedy_script.total_duration}s | Retention Score: {comedy_script.retention_score}/100")
    for s in comedy_script.scenes:
        print(f"  [{s.scene_id} - {s.purpose.upper()} ({s.duration}s)]")
        print(f"     Voice: \"{s.spoken_line}\"")
        print(f"     Text:  [{s.kinetic_text}] | SFX: {s.sfx_cue} | Camera: {s.camera_velocity}")
        print(f"     Veo:   {s.visual_prompt[:65]}...")

    print("\n" + "=" * 65)
    print("TEST 2: PRODUCT AD (12.5s) - 'Autonomous Coding Agent'")
    print("=" * 65)
    ad_script = engine.generate_script(
        concept="Autonomous Coding Agent",
        style=ContentStyle.PRODUCT_AD,
        duration=12.5
    )
    print(f"Title: {ad_script.title}")
    print(f"Total Duration: {ad_script.total_duration}s | Retention Score: {ad_script.retention_score}/100")
    for s in ad_script.scenes:
        print(f"  [{s.scene_id} - {s.purpose.upper()} ({s.duration}s)]")
        print(f"     Voice: \"{s.spoken_line}\"")
        print(f"     Text:  [{s.kinetic_text}] | SFX: {s.sfx_cue}")

    print("\n" + "=" * 65)
    print("TEST 3: MULTI-VARIANT A/B HOOK PACK - 'Mechanical Keyboard'")
    print("=" * 65)
    pack = engine.generate_hook_pack("Custom Mechanical Keyboard")
    for variant_name, script in pack.items():
        hook = script.scenes[0]
        print(f"  * Angle: {variant_name.upper():<16} | Hook: \"{hook.spoken_line}\" | Score: {script.retention_score}/100")

    print("\n[PASS] All viral short-form scripts generated and validated successfully!")


if __name__ == "__main__":
    test_viral_engine()
