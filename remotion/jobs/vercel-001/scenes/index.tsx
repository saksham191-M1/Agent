import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import {enterSpring, scaleIn} from '../../../engine/motion/presets';
import {Captions} from '../../../engine/components/Captions';
import {NoiseTexture} from '../../../engine/components/NoiseTexture';
import {ShapeAccents} from '../../../engine/components/ShapeAccents';
import uiTreeData from '../ui_tree.json';
import brandData from '../brand.json';

const SANS = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const Scene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const tree = uiTreeData as unknown as UITree;
  const brand = brandData as any;
  const nodes = tree.nodes || [];

  // Motion preset: enterSpring
  const entrance = enterSpring(frame, fps);
  const progress = frame / durationInFrames;

  // Match active node to current scene (e.g. "scene_1" -> index 0)
  const matchIdx = scene?.id ? parseInt(scene.id.replace('scene_', ''), 10) - 1 : 0;
  const active = (matchIdx >= 0 && matchIdx < nodes.length ? nodes[matchIdx] : nodes[0]) as VectorNode;

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
        backgroundImage: `radial-gradient(circle at 50% 25%, ${brand.colors?.accent || tokens.colors.accent}20 0%, transparent 65%),
                          radial-gradient(circle at 80% 80%, ${brand.colors?.background2 || tokens.colors.background2} 0%, ${brand.colors?.background || tokens.colors.background} 100%)`,
        overflow: 'hidden',
        fontFamily: SANS,
      }}
    >
      {/* Subtle organic noise texture from @remotion/noise */}
      <NoiseTexture accent={brand.colors?.accent || tokens.colors.accent} opacity={0.07} />

      {/* Floating vector shape accents from @remotion/shapes */}
      <ShapeAccents accent={brand.colors?.accent || tokens.colors.accent} count={4} />

      {/* Subtle developer grid overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          pointerEvents: 'none',
        }}
      />

      {/* Brand accent core glow */}
      <div
        style={{
          position: 'absolute',
          width: 700,
          height: 700,
          borderRadius: '50%',
          backgroundColor: brand.colors?.accent || tokens.colors.accent,
          filter: 'blur(200px)',
          opacity: 0.12,
          top: '5%',
          left: '32%',
          pointerEvents: 'none',
        }}
      />

      {/* Main semantic stage */}
      <div
        style={{
          transform: `scale(${scaleIn(entrance)}) translateY(${(1 - entrance) * 30}px)`,
          opacity: entrance,
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

      {/* Subtitles & Captions */}
      {scene?.captionWords && scene.captionWords.length > 0 && (
        <Captions
          tokens={mergedTokens as any}
          words={scene.captionWords}
          sceneFrame={frame}
          visible={true}
        />
      )}
    </div>
  );
};

export default Scene;
