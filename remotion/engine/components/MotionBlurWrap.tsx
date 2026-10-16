import React from 'react';
import {Trail} from '@remotion/motion-blur';

export interface MotionBlurWrapProps {
  children: React.ReactNode;
  enabled?: boolean;
  layers?: number;
  lagInFrames?: number;
  trailOpacity?: number;
}

export const MotionBlurWrap: React.FC<MotionBlurWrapProps> = ({
  children,
  enabled = true,
  layers = 5,
  lagInFrames = 0.02,
  trailOpacity = 0.45,
}) => {
  if (!enabled) {
    return <>{children}</>;
  }

  return (
    <Trail layers={layers} lagInFrames={lagInFrames} trailOpacity={trailOpacity}>
      {children}
    </Trail>
  );
};
