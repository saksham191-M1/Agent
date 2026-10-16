import React from 'react';
import {evolvePath} from '@remotion/paths';
import {interpolate, useCurrentFrame} from 'remotion';

export interface PathRevealProps {
  path?: string;
  color?: string;
  strokeWidth?: number;
  width?: number;
  height?: number;
  durationFrames?: number;
  delayFrames?: number;
  style?: React.CSSProperties;
}

export const PathReveal: React.FC<PathRevealProps> = ({
  path = 'M 10 35 Q 200 15 400 35 T 800 35',
  color = 'currentColor',
  strokeWidth = 4,
  width = 800,
  height = 70,
  durationFrames = 30,
  delayFrames = 5,
  style,
}) => {
  const frame = useCurrentFrame();

  const progress = interpolate(
    frame,
    [delayFrames, delayFrames + durationFrames],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  const evolved = evolvePath(progress, path);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{overflow: 'visible', ...style}}
    >
      <path
        d={path}
        strokeDasharray={evolved.strokeDasharray}
        strokeDashoffset={evolved.strokeDashoffset}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
