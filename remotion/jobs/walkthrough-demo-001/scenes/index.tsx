import React from 'react';
import type {SceneRendererProps} from '../../../engine';
import {WalkthroughViewport} from '../../../engine/walkthrough/WalkthroughViewport';
import specV2 from '../spec.v2.json';
import type {SoftwareWalkthroughSpec} from '../../../engine/walkthrough/types';

const WalkthroughScene: React.FC<SceneRendererProps> = ({scene: _scene, tokens}) => {
  const spec = specV2 as SoftwareWalkthroughSpec;

  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
      <WalkthroughViewport config={spec.walkthroughConfig} brandAccentColor={tokens.colors.accent} />
    </div>
  );
};

export default WalkthroughScene;
