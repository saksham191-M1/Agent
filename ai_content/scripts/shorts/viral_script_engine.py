import re
import json
import logging
from typing import List, Optional, Dict, Any

from jarvis.ai_content.scripts.shorts.contracts import (
    ShortsScriptContract,
    ShortScene,
    ContentStyle,
    HookArchetype
)
from jarvis.ai_content.scripts.shorts.prompt_templates import (
    HOOK_FORMULAS,
    STYLE_BLUEPRINTS
)
from jarvis.ai_content.scripts.shorts.pacing_validator import RetentionScorer

logger = logging.getLogger(__name__)


class ViralScriptEngine:
    """
    Autonomous engine that generates 10-15s viral shorts, comedy sketches, and product ads.
    Niche-agnostic: adapts dynamically to any prompt or concept.
    """

    def __init__(self):
        pass

    def generate_script(
        self,
        concept: str,
        style: ContentStyle = ContentStyle.PRODUCT_AD,
        hook_archetype: Optional[HookArchetype] = None,
        duration: float = 12.5
    ) -> ShortsScriptContract:
        """
        Generates a validated 10-15s short-form video script.
        """
        blueprint = STYLE_BLUEPRINTS[style]
        archetype = hook_archetype or blueprint["preferred_hook"]

        # Select hook formula
        formulas = HOOK_FORMULAS.get(archetype, HOOK_FORMULAS[HookArchetype.PATTERN_INTERRUPT])
        hook_meta = formulas[0]

        # Structure timing breakdown (normalized to exact target duration)
        raw_durations = [d for _, d in blueprint["structure"]]
        scale = duration / sum(raw_durations)
        scaled_durations = [round(d * scale, 1) for d in raw_durations]
        
        # Adjust rounding drift on the climax scene
        drift = round(duration - sum(scaled_durations), 1)
        scaled_durations[2] = round(scaled_durations[2] + drift, 1)

        # Build Scenes based on style
        scenes: List[ShortScene] = []

        if style == ContentStyle.PRODUCT_AD:
            scenes = [
                ShortScene(
                    scene_id="01",
                    purpose="hook",
                    duration=scaled_durations[0],
                    spoken_line=hook_meta["spoken_template"].format(concept=concept),
                    kinetic_text=hook_meta["kinetic_text"],
                    visual_prompt=f"Explosive macro push-in on futuristic {concept}, volumetric lighting, 9:16 vertical 8k photorealistic",
                    visual_asset_source="google_flow_veo",
                    sfx_cue=hook_meta["sfx"],
                    camera_velocity="explosive_push"
                ),
                ShortScene(
                    scene_id="02",
                    purpose="escalation",
                    duration=scaled_durations[1],
                    spoken_line=f"Standard tools burn hours of wasted effort. {concept} eliminates the friction instantly.",
                    kinetic_text="WASTED EFFORT.",
                    visual_prompt=f"Frustrated creator looking at chaotic error screens, red ambient lighting, fast glitch transition",
                    visual_asset_source="reusable_vault",
                    sfx_cue="whoosh",
                    camera_velocity="whip_pan"
                ),
                ShortScene(
                    scene_id="03",
                    purpose="climax",
                    duration=scaled_durations[2],
                    spoken_line=f"Experience pure velocity. Powered by next-generation intelligence.",
                    kinetic_text="PURE VELOCITY.",
                    visual_prompt=f"Hero showcase of {concept} glowing with iridescent energy beams, sleek metallic reflections, floating particles, 9:16 vertical",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="cinematic_boom",
                    camera_velocity="subtle_orbit"
                ),
                ShortScene(
                    scene_id="04",
                    purpose="loop_cta",
                    duration=scaled_durations[3],
                    spoken_line=f"Link in bio to deploy {concept} right now.",
                    kinetic_text="TRY IT NOW.",
                    visual_prompt=f"Minimalist neon CTA card with vibrant gradient pulse and arrow icon, dark aesthetic",
                    visual_asset_source="reusable_vault",
                    sfx_cue="pop",
                    camera_velocity="static"
                )
            ]

        elif style == ContentStyle.COMEDY_SKETCH:
            scenes = [
                ShortScene(
                    scene_id="01",
                    purpose="hook",
                    duration=scaled_durations[0],
                    spoken_line=f"POV: You trusted {concept} for five seconds.",
                    kinetic_text="NEVER AGAIN.",
                    visual_prompt=f"Extreme close-up of someone smugly tapping on {concept}, bright colorful studio, 9:16 vertical",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="record_scratch",
                    camera_velocity="explosive_push"
                ),
                ShortScene(
                    scene_id="02",
                    purpose="escalation",
                    duration=scaled_durations[1],
                    spoken_line="Everything was completely fine... until it made that noise.",
                    kinetic_text="WHAT WAS THAT?",
                    visual_prompt="Subject freezes in terror as mechanical sparks and smoke humorously puff from object",
                    visual_asset_source="reusable_vault",
                    sfx_cue="glitch",
                    camera_velocity="handheld_shake"
                ),
                ShortScene(
                    scene_id="03",
                    purpose="climax",
                    duration=scaled_durations[2],
                    spoken_line=f"And suddenly, {concept} decided to take over the entire apartment.",
                    kinetic_text="IT EVOLVED.",
                    visual_prompt=f"{concept} with hilarious giant laser eyes glowing menacingly, comedic dramatic lighting, 9:16 vertical",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="vine_boom",
                    camera_velocity="explosive_push"
                ),
                ShortScene(
                    scene_id="04",
                    purpose="loop_cta",
                    duration=scaled_durations[3],
                    spoken_line="Send help. Or send snacks.",
                    kinetic_text="SEND HELP.",
                    visual_prompt="Deadpan stare directly into lens, sudden comedic blackout cut",
                    visual_asset_source="reusable_vault",
                    sfx_cue="pop",
                    camera_velocity="static"
                )
            ]

        elif style == ContentStyle.CURIOSITY_LIFEHACK:
            scenes = [
                ShortScene(
                    scene_id="01",
                    purpose="hook",
                    duration=scaled_durations[0],
                    spoken_line=f"This one hidden {concept} trick feels completely illegal.",
                    kinetic_text="FEELS ILLEGAL.",
                    visual_prompt=f"Secret vault opening with glowing violet light revealing {concept}, 9:16 vertical 8k",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="whoosh",
                    camera_velocity="explosive_push"
                ),
                ShortScene(
                    scene_id="02",
                    purpose="escalation",
                    duration=scaled_durations[1],
                    spoken_line="Most people spend hours doing this the hard way every single day.",
                    kinetic_text="THE HARD WAY.",
                    visual_prompt="Frustrated hands typing frantically on keyboard, motion blurred chaos",
                    visual_asset_source="reusable_vault",
                    sfx_cue="glitch",
                    camera_velocity="whip_pan"
                ),
                ShortScene(
                    scene_id="03",
                    purpose="climax",
                    duration=scaled_durations[2],
                    spoken_line=f"Just tap this, activate {concept}, and watch it solve itself in seconds.",
                    kinetic_text="SOLVED IN SECONDS.",
                    visual_prompt=f"Holographic interface resolving seamlessly around {concept}, glowing emerald confirmation tick, 9:16 vertical",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="cinematic_boom",
                    camera_velocity="subtle_orbit"
                ),
                ShortScene(
                    scene_id="04",
                    purpose="loop_cta",
                    duration=scaled_durations[3],
                    spoken_line="Save this before it gets patched.",
                    kinetic_text="SAVE THIS NOW.",
                    visual_prompt="Bookmark icon glowing with sound pulse on dark backdrop",
                    visual_asset_source="reusable_vault",
                    sfx_cue="pop",
                    camera_velocity="static"
                )
            ]

        else: # RELATABLE_POV
            scenes = [
                ShortScene(
                    scene_id="01",
                    purpose="hook",
                    duration=scaled_durations[0],
                    spoken_line=f"That visceral dread when {concept} breaks at 2 AM.",
                    kinetic_text="2 AM NIGHTMARE.",
                    visual_prompt=f"Dramatic red glowing monitor in dark room illuminating exhausted face, 9:16 vertical",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="cinematic_boom",
                    camera_velocity="explosive_push"
                ),
                ShortScene(
                    scene_id="02",
                    purpose="escalation",
                    duration=scaled_durations[1],
                    spoken_line="You stare at the error. The error stares back at you.",
                    kinetic_text="THE ERROR STARES.",
                    visual_prompt="Infinite recursive zoom into blinking red error text",
                    visual_asset_source="reusable_vault",
                    sfx_cue="glitch",
                    camera_velocity="whip_pan"
                ),
                ShortScene(
                    scene_id="03",
                    purpose="climax",
                    duration=scaled_durations[2],
                    spoken_line="Then you change one semicolon and everything magically passes.",
                    kinetic_text="IT WORKED?!",
                    visual_prompt="Heavenly rays of sunlight breaking through clouds over clean glowing code terminal, 9:16 vertical",
                    visual_asset_source="google_flow_veo",
                    sfx_cue="vine_boom",
                    camera_velocity="subtle_orbit"
                ),
                ShortScene(
                    scene_id="04",
                    purpose="loop_cta",
                    duration=scaled_durations[3],
                    spoken_line="Don't ask questions. Just push to prod.",
                    kinetic_text="PUSH TO PROD.",
                    visual_prompt="Green deploy button pressed with glowing sparks",
                    visual_asset_source="reusable_vault",
                    sfx_cue="pop",
                    camera_velocity="static"
                )
            ]

        script = ShortsScriptContract(
            title=f"12s {style.value.replace('_', ' ').title()}: {concept}",
            topic=concept,
            style=style,
            hook_archetype=archetype,
            total_duration=duration,
            aspect_ratio="9:16",
            music_vibe=blueprint["music"],
            scenes=scenes,
            loop_seamless=True
        )

        # Compute Retention Score
        score, breakdown = RetentionScorer.score_script(script)
        script.retention_score = score
        logger.info(f"[ViralScriptEngine] Generated script '{script.title}' with Retention Score: {score}/100")
        for b in breakdown:
            logger.info(f"   {b}")

        return script

    def generate_hook_pack(self, concept: str) -> Dict[str, ShortsScriptContract]:
        """
        Generates 3 distinct viral angles (Product Ad, Comedy Skit, Curiosity Hack)
        for instant A/B testing on Reels/Shorts.
        """
        pack = {
            "product_ad": self.generate_script(concept, style=ContentStyle.PRODUCT_AD, duration=12.5),
            "comedy_sketch": self.generate_script(concept, style=ContentStyle.COMEDY_SKETCH, duration=12.5),
            "curiosity_hack": self.generate_script(concept, style=ContentStyle.CURIOSITY_LIFEHACK, duration=12.5)
        }
        return pack
