import React from 'react';
import {useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
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

  // Continuous subtle camera push (1.00 to 1.05) inspired by twoclipping Opus prompt
  const cameraPush = interpolate(frame, [0, durationInFrames], [1, 1.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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
        backgroundImage: `radial-gradient(circle at 45% 20%, ${brand.colors?.accent || tokens.colors.accent}18 0%, transparent 55%),
                          radial-gradient(circle at 85% 75%, ${brand.colors?.accentLight || tokens.colors.accent}20 0%, transparent 60%),
                          radial-gradient(circle at 50% 95%, ${brand.colors?.background2 || tokens.colors.background2} 0%, ${brand.colors?.background || tokens.colors.background} 100%)`,
        overflow: 'hidden',
        fontFamily: SANS,
        transform: `scale(${cameraPush})`,
      }}
    >
      {/* Subtle organic film grain noise from @remotion/noise */}
      <NoiseTexture accent={brand.colors?.text || tokens.colors.text} opacity={0.06} />

      {/* Floating vector shape accents from @remotion/shapes */}
      <ShapeAccents accent={brand.colors?.accentLight || tokens.colors.accent} count={5} />

      {/* Modern poster grid lines adapted to light cream background */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(to right, rgba(14,15,31,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(14,15,31,0.04) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          pointerEvents: 'none',
        }}
      />

      {/* Instagram signature gradient atmospheric glow */}
      <div
        style={{
          position: 'absolute',
          width: 750,
          height: 750,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${brand.colors?.accent || tokens.colors.accent} 0%, ${brand.colors?.accentLight || tokens.colors.accent} 50%, transparent 70%)`,
          filter: 'blur(220px)',
          opacity: 0.14,
          top: '8%',
          left: '30%',
          pointerEvents: 'none',
        }}
      />

      {/* Main semantic stage */}
      <div
        style={{
          transform: `scale(${scaleIn(entrance)}) translateY(${(1 - entrance) * 32}px)`,
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
