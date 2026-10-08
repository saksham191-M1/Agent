import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import type {Tokens} from '../types';

export const Background: React.FC<{tokens: Tokens; accent?: string; light?: boolean}> = ({tokens, accent = tokens.colors.accent, light = false}) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame % 180, [0, 180], [-4, 4]);
  const base = light ? tokens.colors.background2 : tokens.colors.background;
  return <AbsoluteFill style={{background: `radial-gradient(circle at 80% 18%, ${accent}35, transparent 35%), radial-gradient(circle at 12% 82%, ${tokens.colors.accentLight}20 0%, transparent 68%), ${base}`, overflow: 'hidden'}}>
    <div style={{position: 'absolute', inset: -180, transform: `translate(${drift}px, ${-drift}px)`, opacity: 0.5, background: `radial-gradient(ellipse at 50% 45%, ${accent}15, transparent 55%)`, filter: 'blur(48px)'}} />
    <div style={{position: 'absolute', inset: 0, opacity: 0.045, backgroundImage: `repeating-radial-gradient(circle at 0 0, ${tokens.colors.text} 0 0.7px, transparent 0.7px 4px)`, mixBlendMode: 'screen'}} />
    <div style={{position: 'absolute', inset: 0, boxShadow: `inset 0 0 180px ${tokens.colors.background}6b`}} />
  </AbsoluteFill>;
};
