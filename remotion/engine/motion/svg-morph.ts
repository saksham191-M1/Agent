import {interpolatePath} from '@remotion/paths';
import {easings} from 'animejs';

/**
 * Deterministic path morphing helper.
 * Uses Remotion paths interpolatePath.
 */
export function morphSvgPath(pathA: string, pathB: string, progress: number): string {
  const p = Math.min(1, Math.max(0, progress));
  try {
    return interpolatePath(p, pathA, pathB);
  } catch {
    return p > 0.5 ? pathB : pathA;
  }
}

/**
 * Creates an Anime.js-driven deterministic tween value for a custom curve.
 */
export function animeEase(
  progress: number,
  easing: string = 'linear'
): number {
  const p = Math.min(1, Math.max(0, progress));
  try {
    const fn = (easings as any)?.[easing] || easings.cubicBezier(0.16, 1, 0.3, 1);
    return typeof fn === 'function' ? fn(p) : p;
  } catch {
    return p;
  }
}
