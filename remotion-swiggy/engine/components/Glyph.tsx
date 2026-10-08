import React from 'react';
import type {Tokens} from '../types';

export const Glyph: React.FC<{label: string; tokens: Tokens; accent?: string; size?: number}> = ({label, tokens, accent = tokens.colors.accent, size = 28}) => (
  <span aria-label={label} style={{display: 'inline-grid', placeItems: 'center', width: size, height: size, borderRadius: Math.round(size * .34), color: accent, background: `${accent}16`, border: `1px solid ${accent}45`}}><svg width={Math.round(size * .58)} height={Math.round(size * .58)} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">{label.length % 3 === 0 ? <><circle cx="12" cy="12" r="7" /><path d="M12 5v14M5 12h14" /></> : label.length % 3 === 1 ? <path d="M12 3l3 6 6 3-6 3-3 6-3-6-6-3 6-3 3-6Z" /> : <><rect x="5" y="5" width="14" height="14" rx="3" /><path d="M8 12h8M12 8v8" /></>}</svg></span>
);
