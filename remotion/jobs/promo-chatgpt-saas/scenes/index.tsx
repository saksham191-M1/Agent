import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import uiTreeData from '../ui_tree.json';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const TemplateScene: React.FC<SceneRendererProps> = ({scene: _scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const tree = uiTreeData as unknown as UITree;
  const nodes = tree.nodes || [];

  // Smooth camera entrance spring
  const entrance = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.6},
  });

  const sceneProgress = frame / durationInFrames;
  const activeNodeIdx = Math.min(nodes.length - 1, Math.floor(sceneProgress * nodes.length));
  const activeNode = nodes[activeNodeIdx] as VectorNode;

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
        backgroundColor: tokens.colors.background,
        backgroundImage: `radial-gradient(circle at 50% 30%, ${tokens.colors.accent}18 0%, transparent 70%), radial-gradient(circle at 80% 80%, ${tokens.colors.background2} 0%, ${tokens.colors.background} 100%)`,
        overflow: 'hidden',
        fontFamily: SANS_FONT_STACK,
      }}
    >
      {/* Background Grid Pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      {/* Primary Semantic Stage */}
      <div
        style={{
          transform: `scale(${interpolate(entrance, [0, 1], [0.92, 1])})`,
          opacity: interpolate(entrance, [0, 1], [0, 1]),
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 28,
          zIndex: 10,
        }}
      >
        {activeNode && (
          <VectorRenderer
            node={activeNode}
            tokens={tokens}
            sheenProgress={sceneProgress}
          />
        )}
      </div>

      {/* Floating Accent Glow */}
      <div
        style={{
          position: 'absolute',
          width: 500,
          height: 500,
          borderRadius: '50%',
          backgroundColor: tokens.colors.accent,
          filter: 'blur(160px)',
          opacity: 0.12,
          pointerEvents: 'none',
          top: '20%',
          left: '35%',
        }}
      />
    </div>
  );
};

export default TemplateScene;
