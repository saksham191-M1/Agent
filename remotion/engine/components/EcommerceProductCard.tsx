import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import {enterSpring, scaleIn} from '../motion/presets';

interface EcommerceProductCardProps {
  tokens: Tokens;
  title: string;
  category?: string;
  currentPrice: string;
  originalPrice?: string;
  discountPct?: string;
  rating?: number;
  ratingCount?: string;
  trustBadge?: string;
  deliveryTag?: string;
  accentColor?: string;
  cardBg?: string;
  features?: string[];
  style?: React.CSSProperties;
}

export const EcommerceProductCard: React.FC<EcommerceProductCardProps> = ({
  tokens,
  title,
  category = 'Featured Deal',
  currentPrice,
  originalPrice,
  discountPct,
  rating = 4.8,
  ratingCount = '24,580 ratings',
  trustBadge = 'Assured Quality',
  deliveryTag = 'Free Delivery',
  accentColor,
  cardBg,
  features = ['Fast doorstep delivery', 'Genuine warranty included', 'Top rated by buyers'],
  style,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = enterSpring(frame, fps);
  const floatY = interpolate(frame, [0, 90], [0, -8]);
  const accent = accentColor || tokens.colors.accent;
  const bg = cardBg || tokens.colors.surface;
  const isDark = Boolean(tokens.colors.background && !tokens.colors.background.toLowerCase().startsWith('#f'));

  return (
    <div
      style={{
        width: 640,
        borderRadius: 28,
        background: bg,
        border: `1.5px solid ${tokens.colors.surfaceMuted}22`,
        boxShadow: `0 30px 80px rgba(0,0,0,${isDark ? '0.6' : '0.15'}), 0 4px 16px rgba(0,0,0,0.06)`,
        padding: '32px 36px',
        fontFamily: tokens.fontFamily || 'Inter, sans-serif',
        color: tokens.colors.surfaceText,
        transform: `translateY(${(1 - enter) * 60 + floatY}px) scale(${scaleIn(enter)})`,
        opacity: enter,
        position: 'relative',
        overflow: 'hidden',
        ...style,
      }}
    >
      {/* Top Accent Strip */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 5,
          background: `linear-gradient(90deg, ${accent}, ${tokens.colors.accentLight || accent})`,
        }}
      />

      {/* Header tags row */}
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18}}>
        <div style={{display: 'flex', gap: 8, alignItems: 'center'}}>
          <span
            style={{
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              color: accent,
              background: `${accent}18`,
              padding: '4px 12px',
              borderRadius: 20,
            }}
          >
            {category}
          </span>
          {trustBadge && (
            <span
              style={{
                fontSize: 12,
                fontWeight: 600,
                color: '#16A34A',
                background: '#16A34A18',
                padding: '4px 10px',
                borderRadius: 20,
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              ✓ {trustBadge}
            </span>
          )}
        </div>

        {deliveryTag && (
          <span style={{fontSize: 12, color: tokens.colors.surfaceMuted, fontWeight: 500}}>
            ⚡ {deliveryTag}
          </span>
        )}
      </div>

      {/* Product Title */}
      <div
        style={{
          fontSize: 26,
          fontWeight: 800,
          lineHeight: 1.25,
          color: tokens.colors.surfaceText,
          marginBottom: 12,
          letterSpacing: '-0.02em',
        }}
      >
        {title}
      </div>

      {/* Ratings Row */}
      <div style={{display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20}}>
        <div
          style={{
            background: '#16A34A',
            color: '#FFFFFF',
            fontSize: 13,
            fontWeight: 700,
            padding: '2px 8px',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 3,
          }}
        >
          <span>{rating}</span>
          <span style={{fontSize: 11}}>★</span>
        </div>
        <span style={{fontSize: 13, color: tokens.colors.surfaceMuted}}>
          ({ratingCount})
        </span>
      </div>

      {/* Price Block */}
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          gap: 14,
          padding: '16px 20px',
          borderRadius: 16,
          background: `${tokens.colors.surfaceMuted}0d`,
          border: `1px solid ${tokens.colors.surfaceMuted}1a`,
          marginBottom: 22,
        }}
      >
        <span
          style={{
            fontSize: 38,
            fontWeight: 900,
            color: tokens.colors.surfaceText,
            letterSpacing: '-0.03em',
          }}
        >
          {currentPrice}
        </span>
        {originalPrice && (
          <span
            style={{
              fontSize: 18,
              color: tokens.colors.surfaceMuted,
              textDecoration: 'line-through',
              fontWeight: 500,
            }}
          >
            {originalPrice}
          </span>
        )}
        {discountPct && (
          <span
            style={{
              fontSize: 15,
              fontWeight: 800,
              color: '#16A34A',
              background: '#16A34A1c',
              padding: '3px 10px',
              borderRadius: 8,
              marginLeft: 'auto',
            }}
          >
            {discountPct} OFF
          </span>
        )}
      </div>

      {/* Feature bullets */}
      <div style={{display: 'flex', flexDirection: 'column', gap: 9, marginBottom: 26}}>
        {features.slice(0, 3).map((feat, i) => (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 10, fontSize: 14}}>
            <div
              style={{
                width: 18,
                height: 18,
                borderRadius: '50%',
                background: `${accent}22`,
                color: accent,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 11,
                fontWeight: 800,
                flexShrink: 0,
              }}
            >
              ✓
            </div>
            <span style={{color: tokens.colors.surfaceText, opacity: 0.88}}>{feat}</span>
          </div>
        ))}
      </div>

      {/* Buy Button */}
      <div
        style={{
          height: 52,
          borderRadius: 16,
          background: accent,
          color: '#FFFFFF',
          fontWeight: 800,
          fontSize: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 8px 24px ${accent}44`,
          letterSpacing: '0.01em',
        }}
      >
        Shop Now →
      </div>
    </div>
  );
};
