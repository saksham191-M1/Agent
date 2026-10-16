import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {Glyph} from './Glyph';
import {enterSpring, scaleIn} from '../motion/presets';

export type PhoneItem = {label: string; icon: string};

export const PhoneMockup: React.FC<{tokens: Tokens; items: PhoneItem[]; greeting: string; prompt: string; search: string; style?: React.CSSProperties}> = ({tokens, items, greeting, prompt, search, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = enterSpring(frame, fps);
  const rotate = interpolate(frame, [0, 100], [-5, 4]);
  return <div style={{width: 365, height: 720, borderRadius: 48, padding: 12, background: tokens.colors.surfaceText, border: `2px solid ${tokens.colors.text}33`, boxShadow: `0 35px 85px ${tokens.colors.background}80`, transform: `translateY(${(1 - enter) * 80}px) scale(${scaleIn(enter)}) rotate(${rotate}deg)`, opacity: enter, ...style}}><div style={{position: 'relative', width: '100%', height: '100%', borderRadius: 38, overflow: 'hidden', background: tokens.colors.surface, fontFamily: tokens.fontFamily, color: tokens.colors.surfaceText}}><div style={{height: 48, display: 'flex', alignItems: 'center', padding: '0 18px', fontWeight: 800, color: tokens.colors.accent}}>{tokens.name}<span style={{marginLeft: 'auto', fontSize: 13, color: tokens.colors.surfaceMuted}}>9:41</span></div><div style={{padding: 18}}><div style={{fontSize: 22, fontWeight: 800}}>{greeting}</div><div style={{fontSize: 13, color: tokens.colors.surfaceMuted, marginTop: 5}}>{prompt}</div><div style={{marginTop: 24, height: 58, borderRadius: 18, background: `${tokens.colors.surfaceMuted}16`, display: 'flex', alignItems: 'center', padding: '0 15px', color: tokens.colors.surfaceMuted}}>⌕ {search}</div><div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 20}}>{items.map((item) => <div key={item.label} style={{height: 116, borderRadius: 20, background: `${tokens.colors.surfaceMuted}0d`, padding: 15}}><Glyph label={item.icon} tokens={tokens} size={34} /><div style={{marginTop: 16, fontWeight: 800, fontSize: 15}}>{item.label}</div></div>)}</div></div><div style={{position: 'absolute', width: 341, marginLeft: 12, bottom: 12, height: 58, borderRadius: 20, background: tokens.colors.surface, borderTop: `1px solid ${tokens.colors.surfaceMuted}26`, display: 'flex', justifyContent: 'space-around', alignItems: 'center', color: tokens.colors.surfaceMuted, fontSize: 12}}><span style={{color: tokens.colors.accent}}>Home</span><span>Orders</span><span>Account</span></div></div></div>;
};
