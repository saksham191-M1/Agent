import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';

export const Cursor: React.FC<{tokens: Tokens; from?: [number, number]; to?: [number, number]; start?: number; clickAt?: number}> = ({tokens, from = [22, 84], to = [74, 38], start = 0, clickAt = 48}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - start, fps, config: {damping: 16, stiffness: 150, mass: 0.7}});
  const x = interpolate(Math.min(1, Math.max(0, p)), [0, 1], [from[0], to[0]]);
  const y = interpolate(Math.min(1, Math.max(0, p)), [0, 1], [from[1], to[1]]);
  const click = frame >= clickAt ? spring({frame: frame - clickAt, fps, config: {damping: 13, stiffness: 190}}) : 0;
  return <div style={{position: 'absolute', left: `${x}%`, top: `${y}%`, zIndex: 10, transform: `translate(-3px,-2px) scale(${1 - Math.min(0.12, click * 0.12)})`, filter: `drop-shadow(0 5px 5px ${tokens.colors.background}73)`}}><svg width="46" height="60" viewBox="0 0 46 60" fill="none"><path d="M8 4L38 35L25 36L33 54L24 58L16 39L7 47L8 4Z" fill={tokens.colors.text} stroke={tokens.colors.background} strokeWidth="3" strokeLinejoin="round" />{frame >= clickAt && <circle cx="25" cy="36" r={16 + click * 12} fill="none" stroke={tokens.colors.accent} strokeWidth="3" opacity={Math.max(0, 1 - click)} />}</svg></div>;
};
