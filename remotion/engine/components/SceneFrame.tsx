import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneSpec, Tokens} from '../types';
import {Background} from './Background';
import {BrandLockup} from './BrandLockup';
import {Captions} from './Captions';
import {enterSpring, slideIn} from '../motion/presets';

const fallbackWords = (text: string, duration: number) => text.split(/\s+/).filter(Boolean).map((word, index, words) => ({word, start: Math.round(index / words.length * duration), end: Math.round((index + 1) / words.length * duration)}));

export const SceneFrame: React.FC<React.PropsWithChildren<{scene: SceneSpec; tokens: Tokens; children?: React.ReactNode; light?: boolean}>> = ({scene, tokens, children, light = false}) => {
  const {fps} = useVideoConfig();
  const frame = useCurrentFrame();
  const enter = enterSpring(frame, fps);
  const durationFrames = Math.round(scene.duration * fps);
  const localFrame = Math.min(durationFrames, Math.max(0, frame));
  const exit = interpolate(localFrame, [Math.max(0, durationFrames - 18), durationFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const words = scene.captionWords ?? fallbackWords(scene.caption ?? scene.vo ?? '', durationFrames);
  return <AbsoluteFill style={{fontFamily: tokens.fontFamily, color: tokens.colors.text, opacity: exit}}><Background tokens={tokens} accent={tokens.colors.accent} light={light} /><div style={{position: 'absolute', left: tokens.safe, right: tokens.safe, top: 72, display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: enter}}><BrandLockup tokens={tokens} /><div style={{width: 13, height: 13, borderRadius: '50%', background: tokens.colors.accent, boxShadow: `0 0 24px ${tokens.colors.accent}`}} /></div><div style={{position: 'absolute', top: 190, left: tokens.safe, right: tokens.safe, transform: `translateY(${slideIn(enter)}px)`, opacity: enter}}><div style={{fontSize: 18, textTransform: 'uppercase', letterSpacing: '.24em', fontWeight: 800, color: tokens.colors.accent, marginBottom: 22}}>{scene.id}</div><h1 style={{fontFamily: tokens.displayFontFamily, fontSize: 104, lineHeight: .98, letterSpacing: '-.065em', fontWeight: 800, maxWidth: 930, margin: 0}}>{scene.headline}</h1><p style={{fontSize: 38, lineHeight: 1.15, color: light ? tokens.colors.surfaceMuted : tokens.colors.muted, maxWidth: 850, margin: '28px 0 0', letterSpacing: '-.025em'}}>{scene.subline}</p></div>{children}<Captions tokens={tokens} words={words} sceneFrame={localFrame} visible={Boolean(scene.caption || scene.captionWords || scene.vo)} /></AbsoluteFill>;
};
