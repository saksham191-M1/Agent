import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {enterSpring} from '../motion/presets';

export const CTAButton: React.FC<{tokens: Tokens; label: string; clickFrame?: number; width?: number}> = ({tokens, label, clickFrame = 28, width = 430}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = enterSpring(frame, fps);
  const click = frame >= clickFrame ? spring({frame: frame - clickFrame, fps, config: {damping: 14, stiffness: 190}}) : 0;
  return <div style={{width, height: 92, borderRadius: 46, background: tokens.colors.accent, color: tokens.colors.surfaceText, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: tokens.fontFamily, fontSize: 31, fontWeight: 800, boxShadow: `0 20px 55px ${tokens.colors.accent}48`, transform: `translateY(${(1 - enter) * 32}px) scale(${1 - click * .06})`, opacity: enter}}>{label}<span style={{marginLeft: 18, fontSize: 38}}>↗</span></div>;
};
