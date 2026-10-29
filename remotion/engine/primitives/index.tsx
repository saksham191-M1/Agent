/**
 * remotion/engine/primitives/index.ts
 * ────────────────────────────────────
 * Composable Primitives Architecture & Registry (Phase 6).
 *
 * Provides 9 standard scene primitives:
 * 1. phone_frame      — Configurable mobile frame with sway & responsive sizing
 * 2. browser_frame    — Configurable desktop browser viewport
 * 3. kinetic_headline — Staggered bold kinetic typography (no terminal punctuation)
 * 4. metric_counter   — Animated ease-out stat counter
 * 5. card_grid        — Bento/product cards grid
 * 6. screenshot_pan   — Smooth slow-pan and zoom camera over real screenshot
 * 7. logo_reveal      — Centered brand mark, glow, and call to action
 * 8. feature_list     — Staggered short lines
 * 9. quote_card       — Verified proof-point callout card
 *
 * Includes SlotComposer for placing 1 to 3 primitives in non-overlapping slots:
 * 'full' | 'left' | 'right' | 'overlay'.
 */

import React from 'react';
import { z } from 'zod';
import { interpolate, useCurrentFrame, useVideoConfig, Img } from 'remotion';
import type { Tokens } from '../types';
import { PhoneMockup, type PhoneItem } from '../components/PhoneMockup';
import { BrowserMockup, type BrowserCard } from '../components/BrowserMockup';
import { enterSpring, scaleIn } from '../motion/presets';

export type LayoutSlot = 'full' | 'left' | 'right' | 'overlay';

export interface PrimitiveDefinition<TProps = any> {
  id: string;
  name: string;
  slot: LayoutSlot;
  schema: z.ZodType<TProps>;
  defaultProps: TProps;
  component: React.FC<{
    props: TProps;
    tokens: Tokens;
    style?: React.CSSProperties;
    slot?: LayoutSlot;
  }>;
}

// ──────────────────────────────────────────────────────────────────────────────
// 1. phone_frame
// ──────────────────────────────────────────────────────────────────────────────
export const PhoneFramePropsSchema = z.object({
  width: z.number().default(365),
  height: z.number().default(720),
  sway: z.boolean().default(true),
  greeting: z.string().default('Welcome'),
  prompt: z.string().default(''),
  search: z.string().default('Search...'),
  screenType: z.enum(['grid', 'product_detail', 'checkout', 'feed']).default('grid'),
  items: z.array(z.object({ label: z.string(), icon: z.string().default('') })).default([]),
  navTabs: z.array(z.string()).optional(),
  badges: z.array(z.string()).optional(),
  priceInfo: z.object({
    currentPrice: z.string().nullable().optional(),
    originalPrice: z.string().nullable().optional(),
    discount: z.string().nullable().optional(),
  }).optional(),
});

export type PhoneFrameProps = z.infer<typeof PhoneFramePropsSchema>;

const PhoneFrameComponent: React.FC<{ props: PhoneFrameProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const swayAngle = props.sway ? Math.sin(frame / 20) * 2 : 0;
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', ...style }}>
      <div style={{ transform: `rotate(${swayAngle}deg)`, transformOrigin: 'center center' }}>
        <PhoneMockup
          tokens={tokens}
          items={props.items as PhoneItem[]}
          greeting={props.greeting}
          prompt={props.prompt}
          search={props.search}
          screenType={props.screenType}
          navTabs={props.navTabs}
          badges={props.badges}
          priceInfo={props.priceInfo}
          style={{ width: props.width, height: props.height }}
        />
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 2. browser_frame
// ──────────────────────────────────────────────────────────────────────────────
export const BrowserFramePropsSchema = z.object({
  width: z.number().default(930),
  height: z.number().default(780),
  title: z.string().default('Dashboard'),
  detail: z.string().default(''),
  location: z.string().default(''),
  cards: z.array(z.object({
    label: z.string(),
    detail: z.string(),
    action: z.string(),
    icon: z.string().default(''),
  })).default([]),
  navTabs: z.array(z.string()).optional(),
  showCursor: z.boolean().default(false),
});

export type BrowserFrameProps = z.infer<typeof BrowserFramePropsSchema>;

const BrowserFrameComponent: React.FC<{ props: BrowserFrameProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', ...style }}>
      <BrowserMockup
        tokens={tokens}
        title={props.title}
        detail={props.detail}
        location={props.location}
        cards={props.cards as BrowserCard[]}
        navTabs={props.navTabs}
        showCursor={props.showCursor}
        style={{ width: props.width, height: props.height }}
      />
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 3. kinetic_headline
// ──────────────────────────────────────────────────────────────────────────────
export const KineticHeadlinePropsSchema = z.object({
  headline: z.string(),
  subline: z.string().nullable().optional(),
  fontSize: z.number().default(88),
  align: z.enum(['left', 'center', 'right']).default('center'),
});

export type KineticHeadlineProps = z.infer<typeof KineticHeadlinePropsSchema>;

const KineticHeadlineComponent: React.FC<{ props: KineticHeadlineProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = enterSpring(frame, fps);

  // Guarantee no terminal punctuation on headline
  const cleanHeadline = props.headline.replace(/[.:;!?]+$/, '').trim();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: props.align === 'left' ? 'flex-start' : props.align === 'right' ? 'flex-end' : 'center',
        textAlign: props.align,
        padding: '0 40px',
        height: '100%',
        ...style,
      }}
    >
      <div
        style={{
          fontFamily: tokens.fontFamily,
          fontSize: props.fontSize,
          fontWeight: 900,
          lineHeight: 1.05,
          color: tokens.colors.text,
          letterSpacing: '-0.03em',
          transform: `translateY(${(1 - enter) * 50}px) scale(${scaleIn(enter)})`,
          opacity: enter,
          textTransform: 'uppercase',
        }}
      >
        {cleanHeadline}
      </div>
      {props.subline && (
        <div
          style={{
            marginTop: 24,
            fontSize: Math.round(props.fontSize * 0.38),
            fontWeight: 500,
            color: tokens.colors.muted,
            lineHeight: 1.4,
            maxWidth: 800,
            transform: `translateY(${(1 - enter) * 30}px)`,
            opacity: interpolate(frame, [5, 25], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {props.subline}
        </div>
      )}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 4. metric_counter
// ──────────────────────────────────────────────────────────────────────────────
export const MetricCounterPropsSchema = z.object({
  value: z.union([z.number(), z.string()]).default('100K+'),
  prefix: z.string().default(''),
  suffix: z.string().default(''),
  label: z.string().default('Active Users'),
});

export type MetricCounterProps = z.infer<typeof MetricCounterPropsSchema>;

const MetricCounterComponent: React.FC<{ props: MetricCounterProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = enterSpring(frame, fps);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 48,
        borderRadius: 32,
        background: `${tokens.colors.surface}cc`,
        border: `1px solid ${tokens.colors.surfaceMuted}33`,
        boxShadow: `0 30px 80px ${tokens.colors.background}99`,
        transform: `scale(${scaleIn(enter)})`,
        opacity: enter,
        ...style,
      }}
    >
      <div
        style={{
          fontSize: 110,
          fontWeight: 900,
          color: tokens.colors.accent,
          lineHeight: 1,
          letterSpacing: '-0.04em',
        }}
      >
        {props.prefix}{props.value}{props.suffix}
      </div>
      <div
        style={{
          marginTop: 18,
          fontSize: 24,
          fontWeight: 600,
          color: tokens.colors.muted,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        {props.label}
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 5. card_grid
// ──────────────────────────────────────────────────────────────────────────────
export const CardGridPropsSchema = z.object({
  cards: z.array(z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    tag: z.string().optional(),
  })).default([]),
  columns: z.number().default(2),
});

export type CardGridProps = z.infer<typeof CardGridPropsSchema>;

const CardGridComponent: React.FC<{ props: CardGridProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${props.columns}, 1fr)`,
        gap: 24,
        padding: 40,
        width: '100%',
        maxWidth: 1100,
        margin: '0 auto',
        ...style,
      }}
    >
      {props.cards.map((c, i) => {
        const stagger = interpolate(frame, [i * 6, i * 6 + 18], [0, 1], { extrapolateRight: 'clamp' });
        return (
          <div
            key={c.title}
            style={{
              padding: 28,
              borderRadius: 24,
              background: tokens.colors.surface,
              border: `1px solid ${tokens.colors.surfaceMuted}26`,
              transform: `translateY(${(1 - stagger) * 40}px)`,
              opacity: stagger,
            }}
          >
            {c.tag && (
              <span
                style={{
                  padding: '4px 10px',
                  borderRadius: 12,
                  fontSize: 12,
                  fontWeight: 700,
                  background: `${tokens.colors.accent}26`,
                  color: tokens.colors.accent,
                }}
              >
                {c.tag}
              </span>
            )}
            <div style={{ fontSize: 22, fontWeight: 800, marginTop: c.tag ? 14 : 0, color: tokens.colors.text }}>
              {c.title}
            </div>
            {c.subtitle && (
              <div style={{ fontSize: 15, color: tokens.colors.muted, marginTop: 8 }}>
                {c.subtitle}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 6. screenshot_pan
// ──────────────────────────────────────────────────────────────────────────────
export const ScreenshotPanPropsSchema = z.object({
  src: z.string(),
  panDirection: z.enum(['up', 'down', 'left', 'right']).default('up'),
  scaleFrom: z.number().default(1.0),
  scaleTo: z.number().default(1.08),
});

export type ScreenshotPanProps = z.infer<typeof ScreenshotPanPropsSchema>;

const ScreenshotPanComponent: React.FC<{ props: ScreenshotPanProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const panOffset = interpolate(frame, [0, 180], [0, 60], { extrapolateRight: 'clamp' });
  const scale = interpolate(frame, [0, 180], [props.scaleFrom, props.scaleTo]);

  const transformStyle =
    props.panDirection === 'up'
      ? `translateY(-${panOffset}px) scale(${scale})`
      : props.panDirection === 'down'
      ? `translateY(${panOffset}px) scale(${scale})`
      : props.panDirection === 'left'
      ? `translateX(-${panOffset}px) scale(${scale})`
      : `translateX(${panOffset}px) scale(${scale})`;

  return (
    <div
      style={{
        position: 'relative',
        width: 1080,
        height: 680,
        borderRadius: 24,
        overflow: 'hidden',
        border: `1px solid ${tokens.colors.surfaceMuted}40`,
        boxShadow: `0 40px 100px ${tokens.colors.background}cc`,
        margin: '0 auto',
        ...style,
      }}
    >
      <Img
        src={props.src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: transformStyle,
          transformOrigin: 'center center',
        }}
      />
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 7. logo_reveal
// ──────────────────────────────────────────────────────────────────────────────
export const LogoRevealPropsSchema = z.object({
  brandName: z.string(),
  logoSrc: z.string().optional(),
  tagline: z.string().optional(),
  ctaText: z.string().default('Get Started'),
});

export type LogoRevealProps = z.infer<typeof LogoRevealPropsSchema>;

const LogoRevealComponent: React.FC<{ props: LogoRevealProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = enterSpring(frame, fps);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        ...style,
      }}
    >
      {props.logoSrc ? (
        <Img
          src={props.logoSrc}
          style={{
            height: 100,
            maxHeight: 120,
            objectFit: 'contain',
            transform: `scale(${scaleIn(enter)})`,
            opacity: enter,
          }}
        />
      ) : (
        <div
          style={{
            fontSize: 72,
            fontWeight: 900,
            color: tokens.colors.accent,
            letterSpacing: '-0.03em',
            transform: `scale(${scaleIn(enter)})`,
            opacity: enter,
          }}
        >
          {props.brandName}
        </div>
      )}

      {props.tagline && (
        <div
          style={{
            marginTop: 20,
            fontSize: 26,
            fontWeight: 600,
            color: tokens.colors.muted,
            opacity: interpolate(frame, [10, 30], [0, 1], { extrapolateRight: 'clamp' }),
          }}
        >
          {props.tagline}
        </div>
      )}

      <div
        style={{
          marginTop: 40,
          padding: '18px 48px',
          borderRadius: 40,
          background: tokens.colors.accent,
          color: tokens.colors.surfaceText,
          fontSize: 22,
          fontWeight: 800,
          boxShadow: `0 15px 40px ${tokens.colors.accent}66`,
          transform: `translateY(${(1 - enter) * 30}px)`,
          opacity: enter,
        }}
      >
        {props.ctaText}
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 8. feature_list
// ──────────────────────────────────────────────────────────────────────────────
export const FeatureListPropsSchema = z.object({
  items: z.array(z.string()).default([]),
  bulletColor: z.string().optional(),
});

export type FeatureListProps = z.infer<typeof FeatureListPropsSchema>;

const FeatureListComponent: React.FC<{ props: FeatureListProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const bullet = props.bulletColor || tokens.colors.accent;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, padding: 32, ...style }}>
      {props.items.map((item, idx) => {
        const enter = interpolate(frame, [idx * 8, idx * 8 + 20], [0, 1], { extrapolateRight: 'clamp' });
        return (
          <div
            key={item}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              fontSize: 28,
              fontWeight: 700,
              color: tokens.colors.text,
              transform: `translateX(${(1 - enter) * -30}px)`,
              opacity: enter,
            }}
          >
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: bullet, flexShrink: 0 }} />
            <span>{item}</span>
          </div>
        );
      })}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// 9. quote_card
// ──────────────────────────────────────────────────────────────────────────────
export const QuoteCardPropsSchema = z.object({
  quote: z.string(),
  source: z.string(),
  author: z.string().optional(),
});

export type QuoteCardProps = z.infer<typeof QuoteCardPropsSchema>;

const QuoteCardComponent: React.FC<{ props: QuoteCardProps; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = enterSpring(frame, fps);

  return (
    <div
      style={{
        padding: '36px 48px',
        borderRadius: 28,
        background: `${tokens.colors.surface}ea`,
        border: `1px solid ${tokens.colors.accent}40`,
        boxShadow: `0 25px 60px ${tokens.colors.background}80`,
        maxWidth: 750,
        transform: `translateY(${(1 - enter) * 40}px)`,
        opacity: enter,
        ...style,
      }}
    >
      <div style={{ fontSize: 32, fontWeight: 700, color: tokens.colors.text, lineHeight: 1.35, fontStyle: 'italic' }}>
        "{props.quote}"
      </div>
      <div style={{ marginTop: 20, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: tokens.colors.accent }} />
        <span style={{ fontSize: 16, fontWeight: 700, color: tokens.colors.accent, textTransform: 'uppercase' }}>
          {props.source}
        </span>
        {props.author && (
          <span style={{ fontSize: 15, color: tokens.colors.muted }}>
            — {props.author}
          </span>
        )}
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// Fallback Primitive for Unknown Types (Graceful Degradation)
// ──────────────────────────────────────────────────────────────────────────────
const FallbackComponent: React.FC<{ props: any; tokens: Tokens; style?: React.CSSProperties }> = ({
  props,
  tokens,
  style,
}) => {
  return (
    <div
      style={{
        padding: 32,
        borderRadius: 20,
        background: tokens.colors.surface,
        color: tokens.colors.text,
        textAlign: 'center',
        ...style,
      }}
    >
      <div style={{ fontSize: 28, fontWeight: 800 }}>{props?.title || tokens.name}</div>
      <div style={{ marginTop: 12, fontSize: 16, color: tokens.colors.muted }}>
        {props?.description || tokens.tagline}
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// Primitive Registry
// ──────────────────────────────────────────────────────────────────────────────
export const PRIMITIVE_REGISTRY: Record<string, PrimitiveDefinition> = {
  phone_frame: {
    id: 'phone_frame',
    name: 'Phone Frame',
    slot: 'left',
    schema: PhoneFramePropsSchema,
    defaultProps: PhoneFramePropsSchema.parse({}),
    component: PhoneFrameComponent,
  },
  browser_frame: {
    id: 'browser_frame',
    name: 'Browser Frame',
    slot: 'full',
    schema: BrowserFramePropsSchema,
    defaultProps: BrowserFramePropsSchema.parse({}),
    component: BrowserFrameComponent,
  },
  kinetic_headline: {
    id: 'kinetic_headline',
    name: 'Kinetic Headline',
    slot: 'full',
    schema: KineticHeadlinePropsSchema,
    defaultProps: KineticHeadlinePropsSchema.parse({ headline: 'HEADLINE' }),
    component: KineticHeadlineComponent,
  },
  metric_counter: {
    id: 'metric_counter',
    name: 'Metric Counter',
    slot: 'right',
    schema: MetricCounterPropsSchema,
    defaultProps: MetricCounterPropsSchema.parse({}),
    component: MetricCounterComponent,
  },
  card_grid: {
    id: 'card_grid',
    name: 'Card Grid',
    slot: 'full',
    schema: CardGridPropsSchema,
    defaultProps: CardGridPropsSchema.parse({}),
    component: CardGridComponent,
  },
  screenshot_pan: {
    id: 'screenshot_pan',
    name: 'Screenshot Pan',
    slot: 'full',
    schema: ScreenshotPanPropsSchema,
    defaultProps: ScreenshotPanPropsSchema.parse({ src: '' }),
    component: ScreenshotPanComponent,
  },
  logo_reveal: {
    id: 'logo_reveal',
    name: 'Logo Reveal',
    slot: 'full',
    schema: LogoRevealPropsSchema,
    defaultProps: LogoRevealPropsSchema.parse({ brandName: 'Brand' }),
    component: LogoRevealComponent,
  },
  feature_list: {
    id: 'feature_list',
    name: 'Feature List',
    slot: 'right',
    schema: FeatureListPropsSchema,
    defaultProps: FeatureListPropsSchema.parse({}),
    component: FeatureListComponent,
  },
  quote_card: {
    id: 'quote_card',
    name: 'Quote Card',
    slot: 'overlay',
    schema: QuoteCardPropsSchema,
    defaultProps: QuoteCardPropsSchema.parse({ quote: 'Verified proof', source: 'Customer review' }),
    component: QuoteCardComponent,
  },
};

// ──────────────────────────────────────────────────────────────────────────────
// SlotComposer Component
// ──────────────────────────────────────────────────────────────────────────────
export interface PrimitiveRef {
  type: string;
  props?: Record<string, any>;
  slot?: LayoutSlot;
}

export const SlotComposer: React.FC<{
  primitives: PrimitiveRef[];
  tokens: Tokens;
}> = ({ primitives, tokens }) => {
  if (!primitives || primitives.length === 0) return null;

  return (
    <div style={{ position: 'relative', width: 1920, height: 1080, overflow: 'hidden' }}>
      {primitives.slice(0, 3).map((ref, idx) => {
        const primDef = PRIMITIVE_REGISTRY[ref.type];
        const Component = primDef ? primDef.component : FallbackComponent;
        const activeSlot = ref.slot || (primDef ? primDef.slot : 'full');

        let slotStyle: React.CSSProperties = {
          position: 'absolute',
          width: '100%',
          height: '100%',
          top: 0,
          left: 0,
        };

        if (activeSlot === 'left') {
          slotStyle = {
            position: 'absolute',
            left: 80,
            top: 0,
            width: 860,
            height: 1080,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          };
        } else if (activeSlot === 'right') {
          slotStyle = {
            position: 'absolute',
            right: 80,
            top: 0,
            width: 860,
            height: 1080,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          };
        } else if (activeSlot === 'overlay') {
          slotStyle = {
            position: 'absolute',
            right: 120,
            bottom: 120,
            zIndex: 10,
          };
        }

        const props = ref.props || (primDef ? primDef.defaultProps : {});

        return (
          <div key={`${ref.type}_${idx}`} style={slotStyle}>
            <Component props={props} tokens={tokens} slot={activeSlot} />
          </div>
        );
      })}
    </div>
  );
};
