import React from 'react';
import {Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import type {
  VectorNode,
  MetricCardNode,
  AssetCardNode,
  BentoGridNode,
  PillTagNode,
  InteractiveInputNode,
  NotificationToastNode,
  ToggleSwitchNode,
  PhoneMockupNode,
  BrowserMockupNode,
  SmartCursorNode,
  CTAButtonNode,
  StatCounterNode,
  EcommerceProductCardNode,
} from './types';
import type {Tokens} from '../types';
import {AnimatedChartView} from './skills/AnimatedChart';
import {KineticTypographyView} from './skills/KineticTypography';
import {MessagingChatView} from './skills/MessagingChat';
import {CinematicAppFrameView} from './skills/CinematicAppFrame';
import {SmartCursor} from './skills/SmartCursor';
import {PhoneMockup} from '../components/PhoneMockup';
import {BrowserMockup} from '../components/BrowserMockup';
import {CTAButton} from '../components/CTAButton';
import {StatCounter} from '../components/StatCounter';
import {EcommerceProductCard} from '../components/EcommerceProductCard';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const getFontFamily = (tokens: Tokens) => (tokens?.fontFamily ? `${tokens.fontFamily}, ${SANS_FONT_STACK}` : SANS_FONT_STACK);
const getDisplayFontFamily = (tokens: Tokens) => (tokens?.displayFontFamily ? `${tokens.displayFontFamily}, ${SANS_FONT_STACK}` : SANS_FONT_STACK);

/**
 * Specular sheen wiping across card surface upon camera entry or focal lock-in
 */
export const SpecularSheen: React.FC<{progress?: number}> = ({progress = 0}) => {
  const p = Math.min(1, Math.max(0, progress));
  if (p <= 0 || p >= 1) return null;
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: 'linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.08) 50%, transparent 70%)',
        transform: `translateX(${-100 + p * 250}%)`,
        pointerEvents: 'none',
        zIndex: 5,
      }}
    />
  );
};

/**
 * Optical depth-of-field distance blur based on camera distance to focal plane
 */
export function computeDofBlur(
  nodePosition: [number, number, number] | undefined,
  cameraPosition?: [number, number, number],
  cameraTarget?: [number, number, number]
): number {
  if (!nodePosition || !cameraPosition) return 0;
  const [nx, ny, nz] = nodePosition;
  const [cx, cy, cz] = cameraPosition;

  let deltaZ: number;
  if (cameraTarget) {
    const focalDist = Math.hypot(cx - cameraTarget[0], cy - cameraTarget[1], cz - cameraTarget[2]);
    const nodeDist = Math.hypot(cx - nx, cy - ny, cz - nz);
    deltaZ = Math.abs(nodeDist - focalDist);
  } else {
    const nodeDist = Math.hypot(cx - nx, cy - ny, cz - nz);
    const estFocus = Math.abs(cz);
    deltaZ = Math.abs(nodeDist - estFocus);
  }

  const rawBlur = (deltaZ - 200) * 0.02;
  return Math.min(16, Math.max(0, rawBlur));
}

/**
 * Metric Card with smooth SVG Bezier sparkline and pulsing status chip
 */
export const MetricCardView: React.FC<{
  node: MetricCardNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = node.accentColor || tokens.colors.accent;
  const points = node.chartPoints && node.chartPoints.length > 1 ? node.chartPoints : [20, 45, 80, 110, 140];
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  const width = 280;
  const height = 70;
  const step = width / (points.length - 1);

  // Smooth SVG cubic Bezier curve generation
  const coords = points.map((p, idx) => ({
    x: idx * step,
    y: height - ((p - min) / range) * (height - 14) - 7,
  }));

  let pathD = `M ${coords[0].x} ${coords[0].y}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const p0 = coords[i];
    const p1 = coords[i + 1];
    const cpX = (p0.x + p1.x) / 2;
    pathD += ` C ${cpX} ${p0.y}, ${cpX} ${p1.y}, ${p1.x} ${p1.y}`;
  }

  // Spring entrance
  const entrance = spring({
    frame,
    fps,
    config: {damping: 12, mass: 0.5},
  });

  return (
    <div
      style={{
        width: 360,
        padding: '24px 28px',
        borderRadius: 24,
        background: 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)',
        border: '1px solid rgba(255,255,255,0.14)',
        boxShadow: '0 24px 60px rgba(0,0,0,0.5)',
        backdropFilter: 'blur(24px)',
        filter: dofFilter,
        position: 'relative',
        overflow: 'hidden',
        color: tokens.colors.text,
        fontFamily: getFontFamily(tokens),
        transform: `scale(${interpolate(entrance, [0, 1], [0.95, 1])})`,
        opacity: entrance,
      }}
    >
      <SpecularSheen progress={sheenProgress} />
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12}}>
        <span style={{fontSize: 14, fontWeight: 600, color: tokens.colors.muted, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: getFontFamily(tokens)}}>
          {node.label}
        </span>
        {node.delta && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 13,
              fontWeight: 700,
              color: '#10b981',
              background: 'rgba(16,185,129,0.14)',
              border: '1px solid rgba(16,185,129,0.3)',
              padding: '4px 10px',
              borderRadius: 14,
              fontFamily: getFontFamily(tokens),
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                backgroundColor: '#10b981',
                boxShadow: '0 0 8px #10b981',
              }}
            />
            <span>{node.delta}</span>
          </div>
        )}
      </div>

      <div style={{fontSize: 42, fontWeight: 800, letterSpacing: '-0.03em', marginBottom: 16, fontFamily: getDisplayFontFamily(tokens)}}>
        {node.value}
      </div>

      <svg width={width} height={height} style={{overflow: 'visible'}}>
        <defs>
          <linearGradient id={`grad-${node.id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={accent} stopOpacity={0.45} />
            <stop offset="100%" stopColor={accent} stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <path d={`${pathD} L ${width} ${height} L 0 ${height} Z`} fill={`url(#grad-${node.id})`} />
        <path d={pathD} fill="none" stroke={accent} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

/**
 * Asset Card with Glassmorphic Frame
 */
export const AssetCardView: React.FC<{
  node: AssetCardNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const assetSrc =
    node.assetUrl.startsWith('http://') || node.assetUrl.startsWith('https://') || node.assetUrl.startsWith('data:')
      ? node.assetUrl
      : staticFile(node.assetUrl.replace(/^\/?public\//, '').replace(/^\//, ''));

  return (
    <div
      style={{
        width: 380,
        borderRadius: 24,
        overflow: 'hidden',
        position: 'relative',
        background: 'linear-gradient(135deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.02) 100%)',
        border: '1px solid rgba(255,255,255,0.14)',
        boxShadow: '0 24px 60px rgba(0,0,0,0.5)',
        backdropFilter: 'blur(24px)',
        filter: dofFilter,
        fontFamily: getFontFamily(tokens),
      }}
    >
      <SpecularSheen progress={sheenProgress} />
      <div style={{height: 180, position: 'relative', overflow: 'hidden', background: '#0a0a0f', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Img
          src={assetSrc}
          alt={node.title || 'Asset'}
          style={{
            maxWidth: '85%',
            maxHeight: '85%',
            objectFit: node.scaleMode,
          }}
        />
      </div>
      {(node.title || node.subtitle) && (
        <div style={{padding: '18px 24px'}}>
          {node.title && <div style={{fontSize: 20, fontWeight: 700, color: tokens.colors.text, fontFamily: getFontFamily(tokens)}}>{node.title}</div>}
          {node.subtitle && <div style={{fontSize: 14, color: tokens.colors.muted, marginTop: 4, fontFamily: getFontFamily(tokens)}}>{node.subtitle}</div>}
        </div>
      )}
    </div>
  );
};

/**
 * Bento Grid View with Sub-pixel Borders and Soft Shadows
 */
export const BentoGridView: React.FC<{
  node: BentoGridNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => (
  <div
    style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${node.columns}, 1fr)`,
      gap: node.gap || 18,
      width: 760,
      filter: dofFilter,
      fontFamily: getFontFamily(tokens),
    }}
  >
    {node.cards.map((card) => (
      <div
        key={card.id}
        style={{
          padding: '24px 26px',
          borderRadius: 22,
          position: 'relative',
          overflow: 'hidden',
          background: 'linear-gradient(135deg, rgba(255,255,255,0.07) 0%, rgba(255,255,255,0.02) 100%)',
          border: '1px solid rgba(255,255,255,0.12)',
          boxShadow: '0 18px 45px rgba(0,0,0,0.4)',
          backdropFilter: 'blur(20px)',
          gridColumn: card.colSpan ? `span ${card.colSpan}` : undefined,
          gridRow: card.rowSpan ? `span ${card.rowSpan}` : undefined,
          fontFamily: getFontFamily(tokens),
        }}
      >
        <SpecularSheen progress={sheenProgress} />
        <div style={{fontSize: 20, fontWeight: 700, color: tokens.colors.text, fontFamily: getFontFamily(tokens)}}>{card.title}</div>
        <div style={{fontSize: 14, color: tokens.colors.muted, marginTop: 6, lineHeight: 1.4, fontFamily: getFontFamily(tokens)}}>{card.subtitle}</div>
        {card.metric && (
          <div style={{marginTop: 16, fontSize: 30, fontWeight: 800, color: card.accent || tokens.colors.accentLight, fontFamily: getDisplayFontFamily(tokens)}}>
            {card.metric}
          </div>
        )}
      </div>
    ))}
  </div>
);

/**
 * Pill Tag with Live Pulsing Indicator Dot
 */
export const PillTagView: React.FC<{
  node: PillTagNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const accent = node.accent || tokens.colors.accent;
  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 22px',
        borderRadius: 40,
        position: 'relative',
        overflow: 'hidden',
        background: node.variant === 'solid' ? accent : 'rgba(255,255,255,0.08)',
        border: `1px solid ${node.variant === 'outline' ? accent : 'rgba(255,255,255,0.18)'}`,
        boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
        backdropFilter: 'blur(16px)',
        filter: dofFilter,
        color: node.variant === 'solid' ? '#000' : tokens.colors.text,
        fontSize: 15,
        fontWeight: 600,
        fontFamily: getFontFamily(tokens),
      }}
    >
      <SpecularSheen progress={sheenProgress} />
      <span
        style={{
          width: 8,
          height: 8,
          borderRadius: '50%',
          backgroundColor: 'rgb(16, 185, 129)',
          boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)',
          display: 'inline-block',
        }}
      />
      <span>{node.text}</span>
    </div>
  );
};

/**
 * macOS / IDE Window Chrome Terminal with Traffic Lights and Code Syntax Styling
 */
export const InteractiveInputView: React.FC<{
  node: InteractiveInputNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const frame = useCurrentFrame();
  const code = node.typedValue || node.placeholder;
  const cursorBlink = Math.sin(frame * 0.25) > 0;

  // Simple tokenized code styling
  const renderHighlightedCode = (text: string) => {
    const parts = text.split(/(\b(?:const|let|var|await|async|import|from|SELECT|FROM|WHERE|INSERT|INTO|UPDATE)\b|'[^']*'|"[^"]*"|\{|\}|\(|\)|;|:)/g);
    return parts.map((part, idx) => {
      if (/^(const|let|var|await|async|import|from|SELECT|FROM|WHERE|INSERT|INTO|UPDATE)$/.test(part)) {
        return <span key={idx} style={{color: tokens.colors.accent, fontWeight: 700}}>{part}</span>;
      }
      if (/^('[^']*'|"[^"]*")$/.test(part)) {
        return <span key={idx} style={{color: '#34d399'}}>{part}</span>;
      }
      if (/^(\{|\}|\(|\)|;|:)$/.test(part)) {
        return <span key={idx} style={{color: tokens.colors.muted}}>{part}</span>;
      }
      return <span key={idx} style={{color: tokens.colors.text}}>{part}</span>;
    });
  };

  return (
    <div
      style={{
        width: 720,
        borderRadius: 20,
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, rgba(20,24,36,0.92) 0%, rgba(10,12,18,0.96) 100%)',
        border: '1px solid rgba(255,255,255,0.16)',
        boxShadow: '0 30px 80px rgba(0,0,0,0.6)',
        backdropFilter: 'blur(24px)',
        filter: dofFilter,
        fontFamily: getFontFamily(tokens),
      }}
    >
      <SpecularSheen progress={sheenProgress} />
      {/* macOS Window Chrome Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 18px',
          background: 'rgba(255,255,255,0.03)',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        {/* macOS Traffic Light Buttons */}
        <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
          <span style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ff5f56', border: '1px solid rgba(0,0,0,0.15)'}} />
          <span style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ffbd2e', border: '1px solid rgba(0,0,0,0.15)'}} />
          <span style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#27c93f', border: '1px solid rgba(0,0,0,0.15)'}} />
        </div>

        {/* Tab Header Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 12px',
            borderRadius: 8,
            background: 'rgba(255,255,255,0.06)',
            fontSize: 12,
            color: tokens.colors.muted,
            fontFamily: 'Consolas, Monaco, monospace',
          }}
        >
          <span>query.ts</span>
        </div>

        <div style={{width: 50}} />
      </div>

      {/* Editor Body */}
      <div
        style={{
          padding: '20px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontFamily: 'Consolas, Monaco, monospace',
          fontSize: 16,
          lineHeight: 1.6,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 14, flex: 1, overflow: 'hidden'}}>
          {/* Line number gutter */}
          <span style={{color: '#475569', userSelect: 'none', fontSize: 14}}>1</span>
          <div style={{display: 'flex', alignItems: 'center', gap: 2, overflow: 'hidden', whiteSpace: 'nowrap'}}>
            {renderHighlightedCode(code)}
            <span
              style={{
                width: 2,
                height: 20,
                backgroundColor: tokens.colors.accent,
                display: 'inline-block',
                marginLeft: 2,
                opacity: cursorBlink ? 1 : 0,
              }}
            />
          </div>
        </div>

        {/* Action Button Pill */}
        {node.buttonLabel && (
          <div
            style={{
              padding: '10px 24px',
              borderRadius: 14,
              background: `linear-gradient(135deg, ${tokens.colors.accent} 0%, ${tokens.colors.accentLight || tokens.colors.accent} 100%)`,
              color: tokens.colors.surfaceText,
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: '0.02em',
              boxShadow: `0 8px 24px ${tokens.colors.accent}33`,
              marginLeft: 16,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              fontFamily: getFontFamily(tokens),
            }}
          >
            {node.buttonLabel}
          </div>
        )}
      </div>
    </div>
  );
};

export const NotificationToastView: React.FC<{
  node: NotificationToastNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => (
  <div
    style={{
      width: 380,
      padding: '18px 22px',
      borderRadius: 18,
      position: 'relative',
      overflow: 'hidden',
      background: 'rgba(20,24,38,0.92)',
      border: '1px solid rgba(255,255,255,0.14)',
      display: 'flex',
      gap: 16,
      alignItems: 'center',
      boxShadow: '0 20px 45px rgba(0,0,0,0.5)',
      filter: dofFilter,
      fontFamily: getFontFamily(tokens),
    }}
  >
    <SpecularSheen progress={sheenProgress} />
    {node.avatarUrl && (
      <Img src={node.avatarUrl} alt="Avatar" style={{width: 44, height: 44, borderRadius: '50%', objectFit: 'cover'}} />
    )}
    <div style={{flex: 1}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <span style={{fontSize: 16, fontWeight: 700, color: tokens.colors.text, fontFamily: getFontFamily(tokens)}}>{node.title}</span>
        <span style={{fontSize: 12, color: tokens.colors.muted, fontFamily: getFontFamily(tokens)}}>{node.timeAgo}</span>
      </div>
      <div style={{fontSize: 14, color: tokens.colors.muted, marginTop: 4, fontFamily: getFontFamily(tokens)}}>{node.description}</div>
    </div>
  </div>
);

export const ToggleSwitchView: React.FC<{
  node: ToggleSwitchNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const accent = node.activeColor || tokens.colors.accent;
  const isActive = node.state === 'active';

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 14,
        padding: '12px 20px',
        borderRadius: 24,
        background: 'rgba(20,24,38,0.92)',
        border: '1px solid rgba(255,255,255,0.14)',
        boxShadow: '0 12px 30px rgba(0,0,0,0.4)',
        backdropFilter: 'blur(16px)',
        filter: dofFilter,
        fontFamily: getFontFamily(tokens),
      }}
    >
      <SpecularSheen progress={sheenProgress} />
      <span style={{fontSize: 14, fontWeight: 600, color: tokens.colors.text}}>{node.label}</span>
      <div
        style={{
          width: 44,
          height: 24,
          borderRadius: 12,
          backgroundColor: isActive ? accent : 'rgba(255,255,255,0.18)',
          position: 'relative',
        }}
      >
        <div
          style={{
            width: 18,
            height: 18,
            borderRadius: '50%',
            backgroundColor: 'rgb(255, 255, 255)',
            position: 'absolute',
            top: 3,
            left: isActive ? 23 : 3,
            boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
          }}
        />
      </div>
    </div>
  );
};

export interface VectorRendererProps {
  node: VectorNode;
  tokens: Tokens;
  cameraPosition?: [number, number, number];
  cameraTarget?: [number, number, number];
  sheenProgress?: number;
}

export const VectorRenderer: React.FC<VectorRendererProps> = ({
  node,
  tokens,
  cameraPosition,
  cameraTarget,
  sheenProgress = 0,
}) => {
  const blurPx = computeDofBlur(node.position3D, cameraPosition, cameraTarget);
  const dofFilter = blurPx > 0.1 ? `blur(${blurPx.toFixed(1)}px)` : undefined;

  const renderContent = () => {
    switch (node.type) {
    case 'metric_card':
      return <MetricCardView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'asset_card':
      return <AssetCardView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'bento_grid':
      return <BentoGridView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'pill_tag':
      return <PillTagView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'toggle_switch':
      return <ToggleSwitchView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'interactive_input':
      return <InteractiveInputView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'notification_toast':
      return <NotificationToastView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'chart':
      return <AnimatedChartView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'kinetic_typography':
      return <KineticTypographyView node={node} tokens={tokens} dofFilter={dofFilter} />;
    case 'chat_messaging':
      return <MessagingChatView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'app_frame':
      return <CinematicAppFrameView node={node} tokens={tokens} sheenProgress={sheenProgress} dofFilter={dofFilter} />;
    case 'phone_mockup': {
      const phonNode = node as PhoneMockupNode;
      const phonTokens = {
        ...tokens,
        name: (tokens as any).name || 'App',
        fontFamily: tokens.fontFamily || 'Inter, sans-serif',
      };
      return (
        <div style={{filter: dofFilter}}>
          <PhoneMockup
            tokens={phonTokens as any}
            items={phonNode.items}
            greeting={phonNode.greeting}
            prompt={phonNode.prompt}
            search={phonNode.search}
            navTabs={phonNode.navTabs}
            headerBg={phonNode.headerBg}
            headerColor={phonNode.headerColor}
            badges={phonNode.badges}
            priceInfo={phonNode.priceInfo}
            screenType={phonNode.screenType}
          />
        </div>
      );
    }
    case 'ecommerce_product_card': {
      const cardNode = node as EcommerceProductCardNode;
      return (
        <div style={{filter: dofFilter}}>
          <EcommerceProductCard
            tokens={tokens}
            title={cardNode.title}
            category={cardNode.category}
            currentPrice={cardNode.currentPrice}
            originalPrice={cardNode.originalPrice}
            discountPct={cardNode.discountPct}
            rating={cardNode.rating}
            ratingCount={cardNode.ratingCount}
            trustBadge={cardNode.trustBadge}
            deliveryTag={cardNode.deliveryTag}
            accentColor={cardNode.accentColor}
            cardBg={cardNode.cardBg}
            features={cardNode.features}
          />
        </div>
      );
    }
    case 'browser_mockup': {
      const browNode = node as BrowserMockupNode;
      const browTokens = {
        ...tokens,
        name: (tokens as any).name || 'App',
        fontFamily: tokens.fontFamily || 'Inter, sans-serif',
      };
      return (
        <div style={{filter: dofFilter}}>
          <BrowserMockup
            tokens={browTokens as any}
            title={browNode.title}
            detail={browNode.detail}
            location={browNode.location}
            cards={browNode.cards}
            showCursor={browNode.showCursor}
          />
        </div>
      );
    }
    case 'smart_cursor': {
      const cursorNode = node as SmartCursorNode;
      return (
        <SmartCursor
          waypoints={cursorNode.waypoints}
          accentColor={cursorNode.accentColor || tokens.colors.accent}
        />
      );
    }
    case 'cta_button': {
      const cta = node as CTAButtonNode;
      return (
        <div style={{filter: dofFilter}}>
          <CTAButton
            tokens={tokens}
            label={cta.label}
            clickFrame={cta.clickFrame}
            width={cta.width}
          />
        </div>
      );
    }
    case 'stat_counter': {
      const stat = node as StatCounterNode;
      return (
        <div style={{filter: dofFilter}}>
          <StatCounter
            tokens={tokens}
            value={stat.value}
            suffix={stat.suffix || '+'}
            label={stat.label}
            index={stat.index || 0}
          />
        </div>
      );
    }
    default:
      return null;
    }
  };

  const content = renderContent();
  if (!content) return null;

  const [posX = 0, posY = 0, posZ = 0] = node.position3D || [0, 0, 0];
  const [rotX = 0, rotY = 0, rotZ = 0] = node.rotationDeg || [0, 0, 0];
  const scale = node.scale ?? 1;
  const opacity = node.opacity ?? 1;

  const hasTransform = posX !== 0 || posY !== 0 || posZ !== 0 || rotX !== 0 || rotY !== 0 || rotZ !== 0 || scale !== 1 || opacity !== 1;

  if (!hasTransform) {
    return content;
  }

  return (
    <div
      style={{
        transform: `translate3d(${posX}px, ${posY}px, ${posZ}px) rotateX(${rotX}deg) rotateY(${rotY}deg) rotateZ(${rotZ}deg) scale(${scale})`,
        transformStyle: 'preserve-3d',
        opacity,
        willChange: 'transform',
      }}
    >
      {content}
    </div>
  );
};
