import React, {useMemo} from 'react';
import {Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import type {AdSpec, SceneSpec} from '../types';
import {generateProceduralFoley, type FoleyCue} from './foley-scheduler';
import {BeatGridScheduler} from './beat-grid';

const asset = (root: string, file: string) => staticFile(`${root}/${file}`);

export type AudioMode = 'option_a_sfx_v2' | 'option_b_remotion_native' | 'option_c_hybrid';

export const AudioMixer: React.FC<{spec: AdSpec; mode?: AudioMode}> = ({
  spec,
  mode = 'option_c_hybrid',
}) => {
  const {fps, durationInFrames} = useVideoConfig();
  const voice = spec.audio.voice;
  const duckTarget = 1 - (spec.audio.duck ?? 7) / 100;

  // BPM grid quantization for cues and procedural triggers
  const beatScheduler = useMemo(() => new BeatGridScheduler({bpm: spec.bpm || 120, fps}), [spec.bpm, fps]);

  // Generate 2.5D Procedural Foley triggers once per render
  const foleyCues = useMemo(() => generateProceduralFoley(durationInFrames), [durationInFrames]);

  // Frame-based attack & release envelopes for music bed
  const attackFrames = Math.max(1, Math.floor(0.5 * fps));
  const tailFadeFrames = Math.max(1, Math.floor(1.5 * fps));

  // Collect all POP cue frames for -6dB SFX ducking (Rule 3: SFX Beat Engine v2)
  const popFrames = useMemo(() => {
    const frames: number[] = [];
    for (const scene of spec.scenes) {
      for (const cue of scene.sfx || []) {
        if (cue.type.toLowerCase() === 'pop') {
          frames.push(Math.round((scene.start + cue.t) * fps));
        }
      }
    }
    return frames;
  }, [spec.scenes, fps]);

  const musicVolumeFn = (f: number) => {
    let duckingFactor = 1;
    for (const scene of spec.scenes) {
      if (!voice?.clips?.[scene.id]) continue;
      // Voice clip runs from frame 8 to duration - 8
      const clipStart = Math.round(scene.start * fps) + 8;
      const clipEnd = Math.round((scene.start + scene.duration) * fps) - 8;
      const duckAttack = Math.round(0.2 * fps);
      const duckRelease = Math.round(0.5 * fps);

      // Ducking envelope: 0.2s attack, 0.5s release
      if (f >= clipStart - duckAttack && f <= clipEnd + duckRelease) {
        let envelope = 1; // 1 means full ducking
        if (f < clipStart) {
          envelope = Math.max(0, 1 - (clipStart - f) / duckAttack);
        } else if (f > clipEnd) {
          envelope = Math.max(0, 1 - (f - clipEnd) / duckRelease);
        }
        const currentDuck = 1 - (1 - duckTarget) * envelope;
        duckingFactor = Math.min(duckingFactor, currentDuck);
      }
    }

    // Duck music by -6dB (0.501) on every [POP] hit (SFX Engine v2 Hybrid standard)
    if (mode !== 'option_b_remotion_native') {
      const popDuckDuration = Math.round(0.35 * fps);
      const popAttackFrames = Math.max(1, Math.round(0.04 * fps));
      for (const pFrame of popFrames) {
        if (f >= pFrame - popAttackFrames && f <= pFrame + popDuckDuration) {
          let popEnvelope = 1;
          if (f < pFrame) {
            popEnvelope = Math.max(0, 1 - (pFrame - f) / popAttackFrames);
          } else {
            popEnvelope = Math.max(0, 1 - (f - pFrame) / popDuckDuration);
          }
          const currentPopDuck = 1 - (1 - 0.501) * popEnvelope;
          duckingFactor = Math.min(duckingFactor, currentPopDuck);
        }
      }
    }

    const fade =
      Math.min(1, f / attackFrames) *
      Math.min(1, Math.max(0, (durationInFrames - f) / tailFadeFrames));
    return (spec.audio.music.volume ?? 1) * duckingFactor * fade;
  };

  const roomFadeFrames = Math.max(1, Math.floor(0.05 * fps));
  const roomVolumeFn = (f: number) => {
    const fade =
      Math.min(1, f / roomFadeFrames) *
      Math.min(1, Math.max(0, (durationInFrames - f) / roomFadeFrames));
    return (spec.audio.room.volume ?? 0.6) * fade;
  };

  // Map procedural foley cue types to available audio assets
  const resolveFoleyFile = (type: FoleyCue['type']): string | undefined => {
    if (type === 'whoosh') {
      return spec.audio.sfxFiles?.['whoosh'] || spec.audio.sfxFiles?.['swipe'];
    }
    if (type === 'hit') {
      return (
        spec.audio.sfxFiles?.['hit'] ||
        spec.audio.sfxFiles?.['thud'] ||
        spec.audio.sfxFiles?.['logo-sting']
      );
    }
    if (type === 'ui-pop') {
      return spec.audio.sfxFiles?.['pop'] || spec.audio.sfxFiles?.['pop2'];
    }
    return undefined;
  };

  return (
    <>
      {/* 1. Music Bed with Ducking & Frame-Based Envelopes */}
      {Boolean(spec.audio.music?.file && (spec.audio.music.volume ?? 1) > 0) && (
        <Audio
          src={asset(spec.audio.assetsRoot, spec.audio.music.file)}
          volume={musicVolumeFn}
        />
      )}

      {/* 2. Room Tone (Fills digital silence) */}
      {spec.audio.room?.file && (
        <Audio
          src={asset(spec.audio.assetsRoot, spec.audio.room.file)}
          volume={roomVolumeFn}
        />
      )}

      {/* 3. Procedural Foley (2.5D Montage Impacts & Pre-Whooshes) */}
      {foleyCues.map((cue) => {
        const file = resolveFoleyFile(cue.type);
        if (!file) return null;
        const cueDuration = Math.round(1.2 * fps);
        return (
          <Sequence key={`foley-${cue.id}`} from={cue.frame} durationInFrames={cueDuration}>
            <Audio
              src={asset(spec.audio.assetsRoot, file)}
              volume={(localFrame) =>
                cue.volume *
                Math.min(1, localFrame / 4) *
                Math.min(1, Math.max(0, (cueDuration - localFrame) / 16))
              }
            />
          </Sequence>
        );
      })}

      {/* 4. Scene-Specific Voiceover Clips */}
      {mode !== 'option_a_sfx_v2' &&
        spec.scenes.map((scene) => {
          const file = voice?.clips?.[scene.id];
        if (!file) return null;
        const from = Math.round(scene.start * fps) + 8;
        const duration = Math.max(1, Math.round(scene.duration * fps) - 8);
        return (
          <Sequence key={`voice-${scene.id}`} from={from} durationInFrames={duration}>
            <Audio
              src={asset(spec.audio.assetsRoot, file)}
              volume={(localFrame) =>
                0.92 *
                Math.min(1, localFrame / 8) *
                Math.min(1, Math.max(0, (duration - localFrame) / 4))
              }
            />
          </Sequence>
        );
      })}

      {/* 5. Scene-Specific SFX Cues (Quantized to 16th-note BPM grid) */}
      {spec.scenes.flatMap((scene: SceneSpec) =>
        scene.sfx.map((cue, index) => {
          const file = spec.audio.sfxFiles?.[cue.type];
          if (!file) return null;
          const rawFrame = Math.round((scene.start + cue.t) * fps);
          const from = Math.max(0, beatScheduler.snapFrame(rawFrame, 'sixteenth'));
          return (
            <Sequence
              key={`sfx-${scene.id}-${cue.type}-${index}`}
              from={from}
              durationInFrames={Math.round(1.2 * fps)}
            >
              <Audio
                src={asset(spec.audio.assetsRoot, file)}
                volume={(localFrame) =>
                  (cue.gain ?? 0.24) *
                  Math.min(1, localFrame / 4) *
                  Math.min(1, Math.max(0, (36 - localFrame) / 16))
                }
              />
            </Sequence>
          );
        })
      )}
    </>
  );
};

