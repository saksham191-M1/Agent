import React from 'react';
import {Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {AdSpec, SceneSpec} from '../types';

const asset = (root: string, file: string) => staticFile(`${root}/${file}`);

export const AudioMixer: React.FC<{spec: AdSpec}> = ({spec}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const musicWindow = spec.scenes.some((scene) => seconds >= scene.start + .22 && seconds <= scene.start + scene.duration - .18);
  const voice = spec.audio.voice;
  return <>{<Audio src={asset(spec.audio.assetsRoot, spec.audio.music.file)} volume={spec.audio.music.volume * (musicWindow ? 1 - spec.audio.duck / 100 : 1) * Math.min(1, seconds / .5) * Math.min(1, Math.max(0, (spec.durationSec - seconds) / 1.5))} />}<Audio src={asset(spec.audio.assetsRoot, spec.audio.room.file)} volume={spec.audio.room.volume} />{spec.scenes.map((scene) => { const file = voice.clips[scene.id]; if (!file) return null; const from = Math.round(scene.start * fps) + 8; const duration = Math.max(1, Math.round(scene.duration * fps) - 8); return <Sequence key={`voice-${scene.id}`} from={from} durationInFrames={duration}><Audio src={asset(spec.audio.assetsRoot, file)} volume={(localFrame) => .92 * Math.min(1, localFrame / 8) * Math.min(1, Math.max(0, (duration - localFrame) / 4))} /></Sequence>; })}{spec.scenes.flatMap((scene: SceneSpec) => scene.sfx.map((cue, index) => { const file = spec.audio.sfxFiles[cue.type]; if (!file) return null; return <Sequence key={`sfx-${scene.id}-${cue.type}-${index}`} from={Math.round((scene.start + cue.t) * fps)} durationInFrames={Math.round(1.2 * fps)}><Audio src={asset(spec.audio.assetsRoot, file)} volume={(localFrame) => (cue.gain ?? .24) * Math.min(1, localFrame / 4) * Math.min(1, Math.max(0, (36 - localFrame) / 16))} /></Sequence>; }))}</>;
};
