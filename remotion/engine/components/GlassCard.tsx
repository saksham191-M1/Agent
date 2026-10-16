import React from 'react';
import type {Tokens} from '../types';

export const GlassCard: React.FC<React.PropsWithChildren<{tokens: Tokens; style?: React.CSSProperties; accent?: string}>> = ({tokens, children, style, accent = tokens.colors.accent}) => (
  <div style={{background: `linear-gradient(145deg, ${tokens.colors.glass}, ${tokens.colors.glass}55)`, border: `1px solid ${tokens.colors.hairline}`, borderRadius: tokens.radius, boxShadow: `0 26px 70px ${tokens.colors.background}57, inset 0 1px 0 ${tokens.colors.text}14, 0 0 0 1px ${accent}12`, backdropFilter: 'blur(18px)', ...style}}>{children}</div>
);
