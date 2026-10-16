import React from 'react';
import {Lottie, type LottieAnimationData} from '@remotion/lottie';
import {AbsoluteFill} from 'remotion';

export interface LottieOverlayProps {
  animationData: unknown;
  opacity?: number;
  loop?: boolean;
  playbackRate?: number;
  style?: React.CSSProperties;
}

export const LottieOverlay: React.FC<LottieOverlayProps> = ({
  animationData,
  opacity = 1,
  loop = true,
  playbackRate = 1,
  style,
}) => {
  if (!animationData || typeof animationData !== 'object') {
    return null;
  }

  return (
    <AbsoluteFill style={{pointerEvents: 'none', opacity, ...style}}>
      <Lottie
        animationData={animationData as LottieAnimationData}
        loop={loop}
        playbackRate={playbackRate}
      />
    </AbsoluteFill>
  );
};
