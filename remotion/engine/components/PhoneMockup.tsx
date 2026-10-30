import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {Glyph} from './Glyph';
import {enterSpring, scaleIn} from '../motion/presets';
import type {InteractionSpec} from '../interactions';
import {getTypedText, InteractiveToast} from '../interactions';

export type PhoneItem = {label: string; icon: string};

interface PhoneMockupProps {
  tokens: Tokens;
  items: PhoneItem[];
  greeting: string;
  prompt: string;
  search: string;
  navTabs?: string[];
  headerBg?: string;
  headerColor?: string;
  badges?: string[];
  priceInfo?: {currentPrice?: string | null; originalPrice?: string | null; discount?: string | null};
  screenType?: 'grid' | 'product_detail' | 'checkout' | 'feed';
  interactions?: InteractionSpec;
  style?: React.CSSProperties;
}

export const PhoneMockup: React.FC<PhoneMockupProps> = ({
  tokens,
  items,
  greeting,
  prompt,
  search,
  navTabs,
  headerBg,
  headerColor,
  badges = [],
  priceInfo,
  screenType = 'grid',
  interactions,
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = enterSpring(frame, fps);
  const rotate = interpolate(frame, [0, 100], [-4, 3]);

  const activeHeaderBg = headerBg || tokens.colors.surface;
  const activeHeaderColor = headerColor || tokens.colors.accent;
  const activeTabs = navTabs && navTabs.length > 0 ? navTabs.slice(0, 4) : [];

  // 1. Composable Typewriter for mobile search bar
  const typewriterConfig = interactions?.typewriter ?? (search ? {text: search} : {});
  const {text: typedSearch, cursor: cursorBlink} = getTypedText(
    frame,
    typewriterConfig,
    search || `Search ${tokens.name}...`
  );

  // 2. Composable Reactive Target for mobile tap
  const reactiveConfig = interactions?.reactiveTarget ?? {
    targetIndex: 0,
    triggerFrame: 48,
    activeLabel: '✓',
    badgeText: '✓',
    glow: true,
  };
  const targetIdx = reactiveConfig?.targetIndex ?? 0;
  const tapFrame = reactiveConfig?.triggerFrame ?? 48;
  const isTapped = Boolean(reactiveConfig) && frame >= tapFrame;
  const tapCompression = isTapped
    ? interpolate(frame - tapFrame, [0, 5, 15], [0.94, 0.97, 1.0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1.0;
  const showRipple = frame >= tapFrame && frame < tapFrame + 22;
  const rippleScale = interpolate(frame - tapFrame, [0, 22], [0.6, 2.2], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const rippleOpacity = interpolate(frame - tapFrame, [0, 22], [0.8, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        width: 440,
        height: 820,
        borderRadius: 52,
        padding: 14,
        background: tokens.colors.surfaceText,
        border: `2px solid ${tokens.colors.text}33`,
        boxShadow: `0 35px 85px ${tokens.colors.background}80`,
        transform: `translateY(${(1 - enter) * 80 - 30}px) scale(${scaleIn(enter)}) rotate(${rotate}deg)`,
        opacity: enter,
        ...style,
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          borderRadius: 38,
          overflow: 'hidden',
          background: tokens.colors.surface,
          fontFamily: tokens.fontFamily,
          color: tokens.colors.surfaceText,
        }}
      >
        {/* Phone Top Header / Status bar */}
        <div
          style={{
            height: 52,
            display: 'flex',
            alignItems: 'center',
            padding: '0 18px',
            fontWeight: 800,
            background: activeHeaderBg,
            color: activeHeaderColor,
            borderBottom: `1px solid ${tokens.colors.surfaceMuted}20`,
          }}
        >
          <span>{tokens.name}</span>
          <span style={{marginLeft: 'auto', fontSize: 13, color: activeHeaderColor, opacity: 0.8}}>9:41</span>
        </div>

        {/* Phone Body Content */}
        <div style={{padding: 18}}>
          {screenType === 'checkout' ? (
            <div>
              <div style={{fontSize: 20, fontWeight: 800, marginBottom: 4}}>Order Summary</div>
              {greeting && (
                <div style={{fontSize: 12, color: tokens.colors.surfaceMuted, marginBottom: 14}}>
                  {greeting}
                </div>
              )}
              <div
                style={{
                  borderRadius: 16,
                  background: `${tokens.colors.surfaceMuted}12`,
                  padding: 14,
                  marginBottom: 14,
                }}
              >
                <div style={{fontWeight: 700, fontSize: 14}}>{greeting}</div>
                {priceInfo && priceInfo.currentPrice && (
                  <div style={{display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8}}>
                    <span style={{fontSize: 20, fontWeight: 900}}>{priceInfo.currentPrice}</span>
                    {priceInfo.originalPrice && (
                      <span style={{fontSize: 13, color: tokens.colors.surfaceMuted, textDecoration: 'line-through'}}>
                        {priceInfo.originalPrice}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div
                style={{
                  height: 44,
                  borderRadius: 14,
                  background: tokens.colors.accent,
                  color: '#FFFFFF',
                  fontWeight: 800,
                  fontSize: 14,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginTop: 18,
                }}
              >
                Proceed to Pay →
              </div>
            </div>
          ) : (
            <div>
              <div style={{fontSize: 20, fontWeight: 800}}>{greeting}</div>
              <div style={{fontSize: 12, color: tokens.colors.surfaceMuted, marginTop: 4}}>{prompt}</div>

              {/* Badges row if any */}
              {badges.length > 0 && (
                <div style={{display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap'}}>
                  {badges.slice(0, 2).map((b, i) => (
                    <span
                      key={i}
                      style={{
                        fontSize: 10,
                        fontWeight: 700,
                        color: tokens.colors.accent,
                        background: `${tokens.colors.accent}18`,
                        padding: '2px 8px',
                        borderRadius: 10,
                      }}
                    >
                      {b}
                    </span>
                  ))}
                </div>
              )}

              {/* Search bar with Typewriter */}
              <div
                style={{
                  marginTop: 16,
                  height: 48,
                  borderRadius: 16,
                  background: `${tokens.colors.surfaceMuted}16`,
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0 14px',
                  color: tokens.colors.surfaceText,
                  fontSize: 13,
                  border: `1px solid ${tokens.colors.surfaceMuted}30`,
                }}
              >
                <span style={{marginRight: 8, color: tokens.colors.accent}}>⌕</span>
                <span>{typedSearch}</span>
                <span style={{color: tokens.colors.accent, fontWeight: 700}}>{cursorBlink}</span>
              </div>

              {/* Items Grid */}
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 16}}>
                {items.slice(0, 4).map((item, idx) => {
                  const isTargetItem = idx === targetIdx;
                  const itemScale = isTargetItem ? tapCompression : 1.0;
                  const isHighlight = isTargetItem && isTapped;

                  return (
                    <div
                      key={item.label}
                      style={{
                        position: 'relative',
                        height: 108,
                        borderRadius: 18,
                        background: isHighlight ? `${tokens.colors.accent}18` : `${tokens.colors.surfaceMuted}0d`,
                        border: isHighlight ? `1.5px solid ${tokens.colors.accent}` : `1px solid transparent`,
                        boxShadow: isHighlight ? `0 6px 18px ${tokens.colors.accent}25` : 'none',
                        padding: 12,
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        transform: `scale(${itemScale})`,
                        overflow: 'hidden',
                      }}
                    >
                      {/* Ripple effect on tap */}
                      {isTargetItem && showRipple && (
                        <div
                          style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            width: 50,
                            height: 50,
                            marginTop: -25,
                            marginLeft: -25,
                            borderRadius: '50%',
                            background: `${tokens.colors.accent}40`,
                            border: `2px solid ${tokens.colors.accent}`,
                            transform: `scale(${rippleScale})`,
                            opacity: rippleOpacity,
                            pointerEvents: 'none',
                          }}
                        />
                      )}
                      {item.icon ? <Glyph label={item.icon} tokens={tokens} size={30} /> : null}
                      <div style={{fontWeight: 700, fontSize: 13, lineHeight: 1.2}}>
                        {item.label}
                        {isHighlight && (
                          <span style={{marginLeft: 4, fontSize: 10, color: tokens.colors.accent, fontWeight: 800}}>
                            {reactiveConfig?.badgeText || '✓'}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Bottom Nav Bar with Brand Nav Tabs (only when navTabs provided) */}
        {activeTabs.length > 0 && (
          <div
            style={{
              position: 'absolute',
              width: 341,
              marginLeft: 12,
              bottom: 12,
              height: 54,
              borderRadius: 20,
              background: tokens.colors.surface,
              borderTop: `1px solid ${tokens.colors.surfaceMuted}26`,
              display: 'flex',
              justifyContent: 'space-around',
              alignItems: 'center',
              color: tokens.colors.surfaceMuted,
              fontSize: 11,
              fontWeight: 600,
            }}
          >
            {activeTabs.map((tab, idx) => (
              <span
                key={tab}
                style={{
                  color: idx === 0 ? tokens.colors.accent : tokens.colors.surfaceMuted,
                  fontWeight: idx === 0 ? 800 : 500,
                }}
              >
                {tab}
              </span>
            ))}
          </div>
        )}

        {/* Action Consequence: Mobile Toast Notification */}
        {interactions?.toast && (
          <InteractiveToast
            tokens={tokens}
            config={interactions.toast}
            style={{bottom: 74, right: 18, fontSize: 11, padding: '7px 14px'}}
          />
        )}
      </div>
    </div>
  );
};
