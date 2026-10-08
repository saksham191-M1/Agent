import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {staggerSpring} from '../motion/presets';

export const StatCounter: React.FC<{tokens: Tokens; value: number; suffix: string; label: string; index: number}> = ({tokens, value, suffix, label, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = staggerSpring(frame, fps, index);
  const count = Math.round(interpolate(Math.min(1, Math.max(0, enter)), [0, 1], [0, value]));
  return <div style={{flex: 1, minWidth: 0, opacity: enter, transform: `translateY(${(1 - enter) * 40}px)`}}><div style={{fontFamily: tokens.fontFamily, fontSize: 69, lineHeight: 0.95, fontWeight: 800, letterSpacing: '-.07em', color: tokens.colors.text}}>{count}<span style={{color: tokens.colors.accent}}>{suffix}</span></div><div style={{marginTop: 16, fontFamily: tokens.fontFamily, fontSize: 22, lineHeight: 1.2, color: tokens.colors.muted}}>{label}</div></div>;
};
