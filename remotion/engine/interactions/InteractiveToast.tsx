import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Tokens} from '../types';
import type {ToastConfig} from './types';

export const InteractiveToast: React.FC<{
  tokens: Tokens;
  config: ToastConfig;
  style?: React.CSSProperties;
}> = ({tokens, config, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const showAt = config.showAtFrame ?? 56;
  const duration = config.durationFrames ?? 70;

  if (frame < showAt) return null;

  const enter = spring({
    frame: frame - showAt,
    fps,
    config: {damping: 14, stiffness: 180, mass: 0.8},
  });

  const exit = frame > showAt + duration
    ? interpolate(frame - (showAt + duration), [0, 15], [1, 0], {extrapolateRight: 'clamp'})
    : 1;

  const opacity = enter * exit;
  const translateY = (1 - enter) * 20 + (1 - exit) * -10;
  const scale = 0.9 + enter * 0.1;

  const icon = config.icon ?? (config.type === 'alert' ? '⚠' : '✓');

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 24,
        right: 24,
        zIndex: 20,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 18px',
        borderRadius: 24,
        background: `${tokens.colors.surfaceText}f0`,
        color: tokens.colors.surface,
        fontFamily: tokens.fontFamily,
        fontSize: 13,
        fontWeight: 700,
        boxShadow: `0 12px 28px ${tokens.colors.background}66, 0 0 1px ${tokens.colors.accent}`,
        border: `1.5px solid ${tokens.colors.accent}66`,
        transform: `translateY(${translateY}px) scale(${scale})`,
        opacity,
        pointerEvents: 'none',
        ...style,
      }}
    >
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 20,
          height: 20,
          borderRadius: 10,
          background: tokens.colors.accent,
          color: tokens.colors.surfaceText,
          fontSize: 11,
          fontWeight: 900,
        }}
      >
        {icon}
      </span>
      <span>{config.message}</span>
    </div>
  );
};
