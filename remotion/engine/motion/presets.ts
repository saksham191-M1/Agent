import {interpolate, spring} from 'remotion';
import {agencySnapEase, smoothBrakeEase} from './bezier-velocity';

export * from './bezier-velocity';
export * from './physics';
export * from './motion-rules';

export const enterSpring = (frame: number, fps: number, delay = 0) => spring({frame: frame - delay, fps, config: {damping: 15, stiffness: 135}});

export const staggerSpring = (frame: number, fps: number, index: number, step = 5) => enterSpring(frame, fps, 12 + index * step);

export const slideIn = (progress: number, distance = 48) => interpolate(progress, [0, 1], [distance, 0]);

export const scaleIn = (progress: number, from = 0.94) => interpolate(progress, [0, 1], [from, 1]);

/**
 * Agency 85% bezier snap interpolation
 */
export const agencySnapIn = (frame: number, durationFrames: number, delay = 0): number => {
  const t = Math.max(0, Math.min(1, (frame - delay) / durationFrames));
  return agencySnapEase(t);
};

export const smoothBrakeIn = (frame: number, durationFrames: number, delay = 0): number => {
  const t = Math.max(0, Math.min(1, (frame - delay) / durationFrames));
  return smoothBrakeEase(t);
};
