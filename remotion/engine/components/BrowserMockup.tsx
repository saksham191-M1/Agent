import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {GlassCard} from './GlassCard';
import {Cursor} from './Cursor';
import {Glyph} from './Glyph';
import {enterSpring, scaleIn} from '../motion/presets';

export type BrowserCard = {label: string; detail: string; action: string; icon: string};

export const BrowserMockup: React.FC<{
  tokens: Tokens;
  title: string;
  detail: string;
  location?: string;
  cards: BrowserCard[];
  navTabs?: string[];
  showCursor?: boolean;
  style?: React.CSSProperties;
}> = ({tokens, title, detail, location = '', cards, navTabs, showCursor = false, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = enterSpring(frame, fps);
  const push = interpolate(Math.min(1, frame / 120), [0, 1], [1, 1.03]);
  const activeTabs = navTabs && navTabs.length > 0 ? navTabs.slice(0, 4) : [];
  return (
    <div style={{position: 'relative', width: 930, height: 780, transform: `translateY(${(1 - enter) * 60}px) scale(${scaleIn(enter)}) scale(${push})`, opacity: enter, ...style}}>
      <GlassCard tokens={tokens} style={{width: '100%', height: '100%', overflow: 'hidden', padding: 0, background: tokens.colors.surface}}>
        <div style={{height: 60, display: 'flex', alignItems: 'center', padding: '0 25px', background: tokens.colors.surface, borderBottom: `1px solid ${tokens.colors.surfaceMuted}26`, color: tokens.colors.surfaceText, fontFamily: tokens.fontFamily}}>
          <div style={{fontSize: 23, fontWeight: 800, color: tokens.colors.accent}}>{tokens.name}</div>
          {activeTabs.length > 0 && (
            <div style={{marginLeft: 36, display: 'flex', gap: 26, fontSize: 15, color: tokens.colors.surfaceMuted}}>
              {activeTabs.map((tab, i) => (
                <span key={tab} style={{color: i === 0 ? tokens.colors.accent : tokens.colors.surfaceMuted}}>
                  {tab}
                </span>
              ))}
            </div>
          )}
          {location ? <div style={{marginLeft: 'auto', fontSize: 14, color: tokens.colors.surfaceMuted}}>{location}⌄</div> : null}
        </div>
        <div style={{height: 'calc(100% - 60px)', padding: 34, background: `linear-gradient(135deg, ${tokens.colors.surface} 0%, ${tokens.colors.accent}12 100%)`, fontFamily: tokens.fontFamily, color: tokens.colors.surfaceText}}>
          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div>
              <div style={{fontSize: 22, fontWeight: 800}}>{title}</div>
              <div style={{marginTop: 8, fontSize: 15, color: tokens.colors.surfaceMuted}}>{detail}</div>
            </div>
            <div style={{width: 150, height: 40, borderRadius: 20, background: tokens.colors.surface, border: `1px solid ${tokens.colors.surfaceMuted}26`, display: 'flex', alignItems: 'center', padding: '0 16px', color: tokens.colors.surfaceMuted, fontSize: 14}}>
              ⌕ Search
            </div>
          </div>
          <div style={{marginTop: 28, display: 'grid', gridTemplateColumns: `repeat(${Math.min(cards.length, 3)}, 1fr)`, gap: 18}}>
            {cards.map((card, index) => (
              <div key={card.label} style={{height: 310, borderRadius: 20, overflow: 'hidden', background: tokens.colors.surface, border: `1px solid ${tokens.colors.surfaceMuted}20`, boxShadow: `0 13px 24px ${tokens.colors.surfaceText}10`, transform: `translateY(${Math.sin((frame + index * 12) / 14) * 3}px)`}}>
                <div style={{height: 150, background: `linear-gradient(135deg, ${tokens.colors.accent}, ${tokens.colors.accentLight})`, display: 'grid', placeItems: 'center'}}>
                  {card.icon ? <Glyph label={card.icon} tokens={tokens} accent={tokens.colors.surfaceText} size={62} /> : null}
                </div>
                <div style={{padding: 16}}>
                  <div style={{fontSize: 17, fontWeight: 800}}>{card.label}</div>
                  <div style={{marginTop: 8, color: tokens.colors.surfaceMuted, fontSize: 13}}>{card.detail}</div>
                  <div style={{marginTop: 14, color: tokens.colors.accent, fontSize: 13, fontWeight: 800}}>{card.action}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>
      {showCursor && <Cursor tokens={tokens} from={[10, 78]} to={[78, 37]} start={8} clickAt={54} />}
    </div>
  );
};
