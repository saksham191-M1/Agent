import React from 'react';
import {Circle, Star, Triangle, Polygon} from '@remotion/shapes';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

export interface ShapeAccentsProps {
  accent: string;
  count?: number;
}

export const ShapeAccents: React.FC<ShapeAccentsProps> = ({accent, count = 5}) => {
  const frame = useCurrentFrame();

  const shapes = [
    {
      type: 'circle',
      x: 180,
      baseY: 220,
      speed: 0.15,
      size: 32,
      opacity: 0.08,
    },
    {
      type: 'star',
      x: 1720,
      baseY: 180,
      speed: -0.12,
      size: 24,
      opacity: 0.07,
    },
    {
      type: 'triangle',
      x: 280,
      baseY: 880,
      speed: 0.18,
      size: 30,
      opacity: 0.06,
    },
    {
      type: 'polygon',
      x: 1640,
      baseY: 840,
      speed: -0.16,
      size: 28,
      opacity: 0.08,
    },
    {
      type: 'star',
      x: 960,
      baseY: 960,
      speed: 0.1,
      size: 20,
      opacity: 0.05,
    },
  ].slice(0, count);

  return (
    <AbsoluteFill style={{pointerEvents: 'none', overflow: 'hidden'}}>
      {shapes.map((s, idx) => {
        const driftY = interpolate(Math.sin((frame + idx * 30) * s.speed), [-1, 1], [-18, 18]);
        const rot = frame * (idx % 2 === 0 ? 0.3 : -0.3);

        return (
          <div
            key={idx}
            style={{
              position: 'absolute',
              left: s.x,
              top: s.baseY + driftY,
              transform: `rotate(${rot}deg)`,
              opacity: s.opacity,
            }}
          >
            {s.type === 'circle' && (
              <Circle radius={s.size} fill={accent} stroke="none" />
            )}
            {s.type === 'star' && (
              <Star
                innerRadius={s.size * 0.45}
                outerRadius={s.size}
                points={5}
                fill={accent}
                stroke="none"
              />
            )}
            {s.type === 'triangle' && (
              <Triangle length={s.size * 1.6} direction="up" fill={accent} stroke="none" />
            )}
            {s.type === 'polygon' && (
              <Polygon radius={s.size} points={6} fill={accent} stroke="none" />
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
