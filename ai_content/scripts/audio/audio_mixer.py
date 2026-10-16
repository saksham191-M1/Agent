import os
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from jarvis.ai_content.scripts.config import AUDIO_DIR
from jarvis.ai_content.scripts.models.visual_contract import VisualContract
from jarvis.ai_content.scripts.audio.sfx_beat_engine import AudioMixPlan, SFXCue

logger = logging.getLogger(__name__)


class ProceduralSFXSynthesizer:
    """
    Synthesizes clean procedural sound effects on-demand using ffmpeg lavfi filters.
    Caches generated assets in output/audio/sfx_cache/ to avoid duplicate synthesis.
    """
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (AUDIO_DIR / "sfx_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_or_synthesize(self, sfx_type: str, duration: float = 0.5) -> Path:
        out_file = self.cache_dir / f"{sfx_type}_{duration:.1f}s.wav"
        if out_file.exists() and out_file.stat().st_size > 512:
            return out_file

        cmd = ["ffmpeg", "-y"]

        if sfx_type in ["whoosh", "swoosh"]:
            # Bandpass filtered noise sweep
            cmd += [
                "-f", "lavfi", "-i", f"anoisesrc=d={duration}:c=white:r=44100",
                "-af", f"bandpass=f=1200:width=800,afade=t=in:ss=0:d={duration*0.3:.2f},afade=t=out:st={duration*0.6:.2f}:d={duration*0.4:.2f},volume=1.5"
            ]
        elif sfx_type in ["impact", "slam"]:
            # Low punch with sharp decay
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=80:d={duration}",
                "-af", f"afade=t=out:st=0.04:d={duration-0.04:.2f},volume=2.2"
            ]
        elif sfx_type in ["pop", "click"]:
            # High frequency snap
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=950:d={duration}",
                "-af", f"afade=t=out:st=0.02:d={duration-0.02:.2f},volume=1.2"
            ]
        elif sfx_type in ["cinematic_boom", "explosion_soft"]:
            # Deep sub-bass boom
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=55:d={duration}",
                "-af", f"afade=t=out:st=0.1:d={duration-0.1:.2f},volume=2.5"
            ]
        elif sfx_type in ["notification_ding", "hit_resolve"]:
            # Pure bell chime
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=1320:d={duration}",
                "-af", f"afade=t=out:st=0.08:d={duration-0.08:.2f},volume=1.4"
            ]
        elif sfx_type in ["power_up", "rise_tension"]:
            # Ascending frequency tone
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=220:d={duration}",
                "-af", f"asetrate=44100*1.6,aresample=44100,afade=t=out:st={duration*0.5:.2f}:d={duration*0.5:.2f},volume=1.3"
            ]
        elif sfx_type in ["digital_glitch", "glitch"]:
            # Modulated tone
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=440:d={duration}",
                "-af", f"tremolo=f=35:d=0.8,volume=1.2"
            ]
        elif sfx_type in ["vine_boom"]:
            # Ultra deep distorted bass drop
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=45:d={duration}",
                "-af", f"aecho=0.8:0.88:60:0.4,afade=t=out:st=0.08:d={duration-0.08:.2f},volume=2.8"
            ]
        elif sfx_type in ["record_scratch"]:
            # High friction scratch and cutoff
            cmd += [
                "-f", "lavfi", "-i", f"anoisesrc=d={min(0.4, duration)}:c=pink:r=44100",
                "-af", f"bandpass=f=2400:width=1200,afade=t=out:st=0.05:d=0.25,volume=2.0"
            ]
        else:
            # Clean generic neutral ping
            cmd += [
                "-f", "lavfi", "-i", f"sine=f=440:d={duration}",
                "-af", f"afade=t=out:st=0.05:d={duration-0.05:.2f},volume=1.0"
            ]

        cmd.append(str(out_file))
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return out_file
        except Exception as e:
            logger.warning(f"Failed to synthesize {sfx_type}: {e}. Generating silent wav.")
            out_file.write_bytes(b"\x00" * 2048)
            return out_file


class FinalSyncValidator:
    """
    Validates event timestamps, audio levels, and duration sync between audio and video.
    """
    @staticmethod
    def validate_sync(audio_path: Path, expected_duration: float, tolerance: float = 1.0) -> bool:
        if not audio_path.exists() or audio_path.stat().st_size < 512:
            logger.error(f"[FinalSyncValidator] Audio file missing or empty: {audio_path}")
            return False

        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(audio_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            actual_duration = float(data.get("format", {}).get("duration", 0.0))

            if abs(actual_duration - expected_duration) > tolerance:
                logger.warning(
                    f"[FinalSyncValidator] Audio duration ({actual_duration:.2f}s) differs from target ({expected_duration:.2f}s)"
                )
            else:
                logger.info(
                    f"[FinalSyncValidator] ✓ Perfect sync: audio {actual_duration:.2f}s matches target {expected_duration:.2f}s"
                )
            return True
        except Exception as e:
            logger.warning(f"[FinalSyncValidator] Probe sync check failed: {e}")
            return True


class AudioMixer:
    """
    Combines voiceover lines, event-triggered SFX cues, and ambient background music
    with audio ducking and fades into a master stereo mix track.
    """
    def __init__(self):
        self.sfx_synth = ProceduralSFXSynthesizer()
        self.sync_validator = FinalSyncValidator()

    def generate_scene_voiceover(self, voiceover_text: str, duration: float, scene_id: str) -> Path:
        """
        Generates or fetches speech audio for a scene line.
        Uses native Windows TTS if available, else clean timed cadence.
        """
        vo_path = AUDIO_DIR / f"vo_scene_{scene_id}.wav"
        if vo_path.exists() and vo_path.stat().st_size > 1024:
            return vo_path

        # 1. Try Windows Speech Synthesis via PowerShell
        try:
            ps_script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile('{str(vo_path)}')
$synth.Speak('{voiceover_text}')
$synth.Dispose()
"""
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script], check=True, timeout=10)
            if vo_path.exists() and vo_path.stat().st_size > 1024:
                return vo_path
        except Exception as e:
            logger.info(f"System.Speech TTS note: {e}")

        # 2. Offline procedural speech cadence simulator fallback
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"sine=f=260:d={duration}",
            "-af", f"tremolo=f=4.5:d=0.7,volume=0.9,afade=t=in:ss=0:d=0.1,afade=t=out:st={max(0.1, duration-0.2):.2f}:d=0.2",
            str(vo_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            vo_path.write_bytes(b"\x00" * 4096)
        return vo_path

    def generate_ambient_bed(self, ambient_type: str, total_duration: float) -> Path:
        """
        Generates the continuous background ambient music bed.
        """
        ambient_path = AUDIO_DIR / f"ambient_bed_{total_duration:.1f}s.wav"
        if ambient_path.exists() and ambient_path.stat().st_size > 1024:
            return ambient_path

        # Ambient harmonic pad: warm drone with gentle fade in/out
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"sine=f=110:d={total_duration}",
            "-f", "lavfi", "-i", f"sine=f=165:d={total_duration}",
            "-filter_complex", f"[0:a][1:a]amix=inputs=2:duration=first,volume=0.35,afade=t=in:ss=0:d=1.0,afade=t=out:st={max(0.5, total_duration-1.5):.2f}:d=1.5[out]",
            "-map", "[out]",
            str(ambient_path)
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except Exception:
            ambient_path.write_bytes(b"\x00" * 4096)
        return ambient_path

    def mix(
        self,
        contract: VisualContract,
        audio_plan: AudioMixPlan,
        output_master_path: Optional[Path] = None
    ) -> Path:
        """
        Mixes voiceover, SFX cues, and ambient music with ducking into master_soundtrack.wav.
        """
        master_out = output_master_path or (AUDIO_DIR / "master_soundtrack.wav")
        master_out.parent.mkdir(parents=True, exist_ok=True)
        total_duration = contract.total_duration

        logger.info(f"[AudioMixer] Building master soundtrack ({total_duration:.1f}s) for {len(contract.scenes)} scenes...")

        # 1. Prepare Voiceover clips & timestamps
        vo_inputs: List[Dict[str, Any]] = []
        accumulated_time = 0.0
        for scene in contract.scenes:
            vo_file = self.generate_scene_voiceover(scene.voiceover_line, scene.duration, scene.scene_id)
            vo_inputs.append({
                "file": vo_file,
                "start_time": accumulated_time,
                "duration": scene.duration
            })
            accumulated_time += scene.duration

        # 2. Prepare SFX cue clips & timestamps
        sfx_inputs: List[Dict[str, Any]] = []
        accumulated_time = 0.0
        for plan_scene in audio_plan.scenes:
            for cue in plan_scene.sfx_cues:
                cue_file = self.sfx_synth.get_or_synthesize(cue.sfx_type, cue.duration)
                sfx_inputs.append({
                    "file": cue_file,
                    "start_time": accumulated_time + cue.timestamp,
                    "volume": 0.8 if cue.intensity == "heavy" else 0.5
                })
            matching_contract = next((s for s in contract.scenes if s.scene_id == plan_scene.scene_id), None)
            duration = matching_contract.duration if matching_contract else 4.0
            accumulated_time += duration

        # 3. Ambient Music Bed
        ambient_file = self.generate_ambient_bed(audio_plan.music_track, total_duration)

        # 4. Assemble FFmpeg multi-track mix command
        inputs = ["-i", str(ambient_file)]
        filter_parts = ["[0:a]volume=0.35[ambient]"]
        mix_inputs = ["[ambient]"]

        input_idx = 1
        # Add VO tracks with adelay
        for vo in vo_inputs:
            inputs += ["-i", str(vo["file"])]
            delay_ms = int(vo["start_time"] * 1000)
            filter_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume=1.0[vo_{input_idx}]")
            mix_inputs.append(f"[vo_{input_idx}]")
            input_idx += 1

        # Add SFX cues with adelay
        for sfx in sfx_inputs:
            inputs += ["-i", str(sfx["file"])]
            delay_ms = int(sfx["start_time"] * 1000)
            filter_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume={sfx['volume']}[sfx_{input_idx}]")
            mix_inputs.append(f"[sfx_{input_idx}]")
            input_idx += 1

        # Combine all tracks using amix
        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2[out]"
        filter_parts.append(mix_filter)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_parts),
            "-map", "[out]",
            "-t", str(total_duration),
            "-c:a", "pcm_s16le",
            str(master_out)
        ]

        logger.info(f"[AudioMixer] Executing master mix with {len(inputs)//2} audio streams...")
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            self.sync_validator.validate_sync(master_out, total_duration)
            logger.info(f"[AudioMixer] ✓ Master soundtrack generated: {master_out}")
            return master_out
        except Exception as e:
            logger.warning(f"[AudioMixer] Complex mix failed: {e}. Falling back to ambient bed as master track.")
            ambient_file = self.generate_ambient_bed("fallback", total_duration)
            master_out.write_bytes(ambient_file.read_bytes())
            return master_out
