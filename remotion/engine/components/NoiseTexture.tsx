import React, {useMemo} from 'react';
import {noise3D} from '@remotion/noise';
import {AbsoluteFill, useCurrentFrame} from 'remotion';

export interface NoiseTextureProps {
  accent?: string;
  opacity?: number;
  scale?: number;
  seed?: string;
  rows?: number;
  cols?: number;
}

export const NoiseTexture: React.FC<NoiseTextureProps> = ({
  accent = 'currentColor',
  opacity = 0.05,
  scale = 0.12,
  seed = 'brand-noise',
  rows = 18,
  cols = 32,
}) => {
  const frame = useCurrentFrame();

  const points = useMemo(() => {
    const list: Array<{cx: number; cy: number; r: number}> = [];
    const cellW = 1920 / cols;
    const cellH = 1080 / rows;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        list.push({
          cx: c * cellW + cellW / 2,
          cy: r * cellH + cellH / 2,
          r: 1.2,
        });
      }
    }
    return list;
  }, [rows, cols]);

  return (
    <AbsoluteFill style={{pointerEvents: 'none', mixBlendMode: 'screen', opacity}}>
      <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{overflow: 'hidden'}}>
        {points.map((pt, i) => {
          const val = noise3D(seed, (pt.cx / 100) * scale, (pt.cy / 100) * scale, frame * 0.012);
          // Normalize [-1, 1] to [0.1, 1.0]
          const dotOpacity = Math.max(0.05, (val + 1) / 2);
          const radius = pt.r * (0.8 + dotOpacity * 0.8);

          return (
            <circle
              key={i}
              cx={pt.cx}
              cy={pt.cy}
              r={radius}
              fill={accent}
              opacity={dotOpacity}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
