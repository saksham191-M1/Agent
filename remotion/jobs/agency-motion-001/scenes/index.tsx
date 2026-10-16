import React from 'react';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree} from '../../../engine/semantic-ui/types';
import uiTreeData from '../ui_tree.json';

const AgencyMotionScene: React.FC<SceneRendererProps> = ({scene: _scene, tokens}) => {
  const tree = uiTreeData as UITree;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: '#070a14',
        backgroundImage: 'radial-gradient(circle at 50% 30%, rgba(0,242,254,0.12), transparent 70%)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        perspective: '1200px',
      }}
    >
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          transformStyle: 'preserve-3d',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 24,
        }}
      >
        {/* Render Vector & Asset Nodes with continuous 3D transforms */}
        {tree.nodes.map((node) => {
          const [x, y, z] = node.position3D;
          return (
            <div
              key={node.id}
              style={{
                transform: `translate3d(${x}px, ${y}px, ${z}px)`,
                transition: 'transform 0.4s cubic-bezier(0.16, 1.0, 0.3, 1.0)',
              }}
            >
              <VectorRenderer node={node} tokens={tokens} />
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgencyMotionScene;
