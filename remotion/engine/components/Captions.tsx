import React from 'react';
import {interpolate} from 'remotion';
import type {CaptionWord, Tokens} from '../types';

export const Captions: React.FC<{tokens: Tokens; words: CaptionWord[]; sceneFrame: number; visible?: boolean}> = ({tokens, words, sceneFrame, visible = true}) => {
  if (!visible) return null;
  return <div style={{position: 'absolute', bottom: 112, left: tokens.safe, right: tokens.safe, display: 'flex', justifyContent: 'center', zIndex: 20}}><div style={{padding: '14px 22px', borderRadius: 16, background: `${tokens.colors.background}c7`, border: `1px solid ${tokens.colors.hairline}`, maxWidth: 920, fontFamily: tokens.fontFamily, fontSize: 44, lineHeight: 1.15, textAlign: 'center', color: tokens.colors.text, boxShadow: `0 8px 30px ${tokens.colors.background}40`}}>{words.map((item, index) => { const active = sceneFrame >= item.start && sceneFrame <= item.end; const revealed = interpolate(Math.max(0, Math.min(1, (sceneFrame - item.start) / 5)), [0, 1], [0, 1]); return <span key={`${item.word}-${index}`} style={{display: 'inline-block', marginRight: 9, opacity: revealed, color: active ? tokens.colors.accentLight : tokens.colors.text, textShadow: active ? `0 0 18px ${tokens.colors.accent}80` : 'none', fontWeight: active ? 700 : 500}}>{item.word}</span>; })}</div></div>;
};
