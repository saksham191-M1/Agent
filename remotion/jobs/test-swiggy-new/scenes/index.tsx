import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import uiTreeData from '../ui_tree.json';
import brandData from '../brand.json';

const SANS = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const Scene: React.FC<SceneRendererProps> = ({scene: _scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const tree  = uiTreeData as unknown as UITree;
  const brand = brandData as any;
  const nodes = tree.nodes || [];

  // Spring camera entrance
  const entrance = spring({frame, fps, config: {damping: 14, mass: 0.6}});
  const progress = frame / durationInFrames;

  // Show one node at a time, advancing through the tree as scene progresses
  const idx     = Math.min(nodes.length - 1, Math.floor(progress * nodes.length));
  const active  = nodes[idx] as VectorNode;

  // Merge brand colors into tokens so every node gets real brand identity
  const mergedTokens = {
    ...tokens,
    name: brand.name,
    colors: {...tokens.colors, ...brand.colors},
    fontFamily: brand.fonts?.display?.family || tokens.fontFamily,
    displayFontFamily: brand.fonts?.display?.family || tokens.fontFamily,
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        backgroundColor: brand.colors?.background || tokens.colors.background,
        backgroundImage: `radial-gradient(circle at 50% 30%, ${brand.colors?.accent || tokens.colors.accent}18 0%, transparent 70%),
                          radial-gradient(circle at 80% 80%, ${brand.colors?.background2 || tokens.colors.background2} 0%, ${brand.colors?.background || tokens.colors.background} 100%)`,
        overflow: 'hidden',
        fontFamily: SANS,
      }}
    >
      {/* Subtle grid overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          pointerEvents: 'none',
        }}
      />

      {/* Brand accent glow */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          backgroundColor: brand.colors?.accent || tokens.colors.accent,
          filter: 'blur(180px)',
          opacity: 0.1,
          top: '10%',
          left: '30%',
          pointerEvents: 'none',
        }}
      />

      {/* Main semantic stage */}
      <div
        style={{
          transform: `scale(${interpolate(entrance, [0, 1], [0.9, 1])}) translateY(${interpolate(entrance, [0, 1], [40, 0])}px)`,
          opacity: interpolate(entrance, [0, 1], [0, 1]),
          zIndex: 10,
        }}
      >
        {active && (
          <VectorRenderer
            node={active}
            tokens={mergedTokens as any}
            sheenProgress={progress}
          />
        )}
      </div>
    </div>
  );
};

export default Scene;
