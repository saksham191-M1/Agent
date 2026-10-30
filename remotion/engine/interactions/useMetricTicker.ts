import {interpolate} from 'remotion';
import type {MetricTickerConfig} from './types';

export function getTickedMetric(
  frame: number,
  config?: MetricTickerConfig
): {value: string; progress: number} | null {
  if (!config) return null;

  const startFrame = config.startFrame ?? 10;
  const durationFrames = config.durationFrames ?? 35;
  const decimals = config.decimals ?? (Number.isInteger(config.to) ? 0 : 1);

  const raw = interpolate(frame - startFrame, [0, durationFrames], [config.from, config.to], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const progress = interpolate(frame - startFrame, [0, durationFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const formatted = raw.toFixed(decimals);
  const prefix = config.prefix ?? '';
  const suffix = config.suffix ?? '';

  return {
    value: `${prefix}${formatted}${suffix}`,
    progress,
  };
}
