import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {GlassCard} from './GlassCard';
import {Cursor} from './Cursor';
import {Glyph} from './Glyph';
import {enterSpring, scaleIn} from '../motion/presets';
import type {InteractionSpec} from '../interactions';
import {getTypedText, InteractiveToast} from '../interactions';

export type BrowserCard = {label: string; detail: string; action: string; icon: string};

export interface BrowserMockupProps {
  tokens: Tokens;
  title: string;
  detail: string;
  location?: string;
  cards: BrowserCard[];
  navTabs?: string[];
  showCursor?: boolean;
  interactions?: InteractionSpec;
  style?: React.CSSProperties;
}

export const BrowserMockup: React.FC<BrowserMockupProps> = ({
  tokens,
  title,
  detail,
  location = '',
  cards,
  navTabs,
  showCursor = false,
  interactions,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = enterSpring(frame, fps);
  const push = interpolate(Math.min(1, frame / 120), [0, 1], [1, 1.03]);
  const activeTabs = navTabs && navTabs.length > 0 ? navTabs.slice(0, 4) : [];

  // ── 1. Composable Typewriter Search ───────────────────────────────────────
  const typewriterConfig = interactions?.typewriter ?? (showCursor ? {} : false);
  const {text: typedSearch, cursor: cursorBlink} = getTypedText(
    frame,
    typewriterConfig,
    `Search ${tokens.name}...`
  );

  // ── 2. Composable Cursor Glide ────────────────────────────────────────────
  const cursorConfig = interactions?.cursor;
  const shouldShowCursor = showCursor || Boolean(cursorConfig);
  const resolvedCursor = typeof cursorConfig === 'object' ? cursorConfig : {};
  const cursorFrom = resolvedCursor.from ?? [12, 85];
  const cursorTo = resolvedCursor.to ?? [22, 58];
  const cursorStart = resolvedCursor.startFrame ?? 10;
  const clickFrame = resolvedCursor.clickFrame ?? 54;

  // ── 3. Composable Reactive Target (Card reaction) ─────────────────────────
  const reactiveConfig = interactions?.reactiveTarget ?? (shouldShowCursor ? {
    targetIndex: 0,
    triggerFrame: clickFrame,
    activeLabel: 'Opening →',
    badgeText: '● ACTIVE',
    glow: true,
  } : undefined);

  const targetIdx = reactiveConfig?.targetIndex ?? 0;
  const triggerAt = reactiveConfig?.triggerFrame ?? clickFrame;
  const isTargetClicked = Boolean(reactiveConfig) && frame >= triggerAt;
  const clickCompression = isTargetClicked
    ? interpolate(frame - triggerAt, [0, 6, 16], [0.95, 0.98, 1.0], {extrapolateRight: 'clamp'})
    : 1.0;

  return (
    <div
      style={{
        position: 'relative',
        width: 930,
        height: 780,
        transform: `translateY(${(1 - enter) * 60}px) scale(${scaleIn(enter)}) scale(${push})`,
        opacity: enter,
        ...style,
      }}
    >
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
            {/* Dynamic Typewriter Search Bar */}
            <div style={{minWidth: 190, height: 40, borderRadius: 20, background: tokens.colors.surface, border: `1px solid ${tokens.colors.accent}40`, display: 'flex', alignItems: 'center', padding: '0 16px', color: tokens.colors.surfaceText, fontSize: 13, boxShadow: `0 2px 8px ${tokens.colors.accent}15`}}>
              <span style={{marginRight: 6, color: tokens.colors.accent}}>⌕</span>
              <span>{typedSearch}</span>
              <span style={{color: tokens.colors.accent, fontWeight: 700}}>{cursorBlink}</span>
            </div>
          </div>
          <div style={{marginTop: 28, display: 'grid', gridTemplateColumns: `repeat(${Math.min(cards.length, 3)}, 1fr)`, gap: 18}}>
            {cards.map((card, index) => {
              const isTargetCard = index === targetIdx;
              const cardScale = isTargetCard ? clickCompression : 1.0;
              const isHighlight = isTargetCard && isTargetClicked;

              return (
                <div
                  key={card.label}
                  style={{
                    height: 310,
                    borderRadius: 20,
                    overflow: 'hidden',
                    background: tokens.colors.surface,
                    border: isHighlight
                      ? `2px solid ${tokens.colors.accent}`
                      : `1px solid ${tokens.colors.surfaceMuted}20`,
                    boxShadow: isHighlight
                      ? `0 14px 32px ${tokens.colors.accent}33, 0 0 12px ${tokens.colors.accent}40`
                      : `0 13px 24px ${tokens.colors.surfaceText}10`,
                    transform: `translateY(${Math.sin((frame + index * 12) / 14) * 3}px) scale(${cardScale})`,
                    transition: 'border 0.2s, box-shadow 0.2s',
                  }}
                >
                  <div style={{height: 150, background: `linear-gradient(135deg, ${tokens.colors.accent}, ${tokens.colors.accentLight})`, display: 'grid', placeItems: 'center', position: 'relative'}}>
                    {card.icon ? <Glyph label={card.icon} tokens={tokens} accent={tokens.colors.surfaceText} size={62} /> : null}
                    {isHighlight && reactiveConfig?.badgeText && (
                      <div style={{position: 'absolute', top: 12, right: 12, background: 'rgba(0,0,0,0.5)', color: '#FFF', fontSize: 10, padding: '3px 8px', borderRadius: 12, fontWeight: 700}}>
                        {reactiveConfig.badgeText}
                      </div>
                    )}
                  </div>
                  <div style={{padding: 16}}>
                    <div style={{fontSize: 17, fontWeight: 800}}>{card.label}</div>
                    <div style={{marginTop: 8, color: tokens.colors.surfaceMuted, fontSize: 13}}>{card.detail}</div>
                    <div style={{marginTop: 14, color: tokens.colors.accent, fontSize: 13, fontWeight: 800}}>
                      {isHighlight && reactiveConfig?.activeLabel ? reactiveConfig.activeLabel : card.action}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </GlassCard>

      {/* 4. Action Consequence: Floating Toast Notification */}
      {interactions?.toast && (
        <InteractiveToast tokens={tokens} config={interactions.toast} />
      )}

      {/* 5. Composable Cursor Component */}
      {shouldShowCursor && (
        <Cursor
          tokens={tokens}
          from={cursorFrom}
          to={cursorTo}
          start={cursorStart}
          clickAt={clickFrame}
        />
      )}
    </div>
  );
};
