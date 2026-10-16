from pathlib import Path
from typing import Tuple

from jarvis.ai_content.scripts.shorts.contracts import ShortsScriptContract
from jarvis.ai_content.scripts.models.visual_contract import VisualContract, SceneContract, VisualElements, CameraMove
from jarvis.ai_content.scripts.audio.sfx_beat_engine import AudioMixPlan, SceneSFXPlan, SFXCue
from jarvis.ai_content.scripts.audio.audio_mixer import AudioMixer


class ShortsPipelineBridge:
    """
    Bridges a 10-15s ShortsScriptContract into the audio and video assembly pipeline.
    """

    @classmethod
    def to_audio_mix_plan(cls, script: ShortsScriptContract) -> AudioMixPlan:
        scene_plans = []
        for s in script.scenes:
            # Map SFX cue to 0.1s from scene start
            cue = SFXCue(
                timestamp=0.1,
                sfx_type=s.sfx_cue if s.sfx_cue in [
                    "whoosh", "cinematic_boom", "vine_boom", "record_scratch", 
                    "pop", "click", "digital_glitch", "impact"
                ] else "whoosh",
                intensity="heavy" if s.purpose in ["hook", "climax"] else "medium",
                duration=0.6,
                trigger_action=f"{s.purpose} -> {s.kinetic_text}"
            )
            scene_plans.append(SceneSFXPlan(
                scene_id=s.scene_id,
                sfx_cues=[cue],
                ambient_bed=script.music_vibe,
                ambient_volume=0.3
            ))

        return AudioMixPlan(
            scenes=scene_plans,
            music_track=script.music_vibe,
            music_volume=0.35,
            vo_ducking_db=-6.0
        )

    @classmethod
    def to_visual_contract(cls, script: ShortsScriptContract) -> VisualContract:
        contract_scenes = []
        for s in script.scenes:
            contract_scenes.append(SceneContract(
                scene_id=s.scene_id,
                purpose=s.purpose,
                duration=s.duration,
                voiceover_line=s.spoken_line,
                visual_elements=VisualElements(
                    characters=[],
                    key_items=[s.kinetic_text],
                    core_action=s.visual_prompt[:80],
                    visual_setting="High-contrast dynamic vertical set",
                    camera_move=CameraMove(movement="push_in_fast" if s.camera_velocity == "explosive_push" else "static")
                ),
                entity_refs=[]
            ))

        return VisualContract(
            script_id=script.title.replace(" ", "_").lower()[:30],
            total_duration=script.total_duration,
            tts_script_with_breaks=" ".join(s.spoken_line for s in script.scenes),
            tts_tone="energetic",
            music_genre=script.music_vibe,
            energy_curve="slow_build_to_fast",
            entities=[],
            scenes=contract_scenes
        )

    @classmethod
    def render_shorts_soundtrack(cls, script: ShortsScriptContract) -> Path:
        """
        Renders the complete multi-track voiceover + meme/cinematic SFX + music bed
        for the generated short.
        """
        visual_contract = cls.to_visual_contract(script)
        audio_plan = cls.to_audio_mix_plan(script)

        mixer = AudioMixer()
        soundtrack_path = mixer.mix(visual_contract, audio_plan)
        return soundtrack_path
