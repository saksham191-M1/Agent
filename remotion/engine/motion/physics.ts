import {solveCubicBezier} from './bezier-velocity';

/**
 * Agency Kinematics Curves
 * Inspired by high-end motion design and After Effects speed graphs (85% influence).
 */
export const AGENCY_MOTION = {
  // 85% snap curve: explosive initial velocity, smooth resting settle
  BEZIER_SNAP: [0.16, 1, 0.3, 1] as const,

  // High-speed whip pan for camera movements between beats
  WHIP_PAN: [0.7, 0, 0.3, 1] as const,

  // Exponential ease-out for explosive entrances
  EASE_OUT_EXPO: [0.19, 1, 0.22, 1] as const,

  // Smooth cinematic drift for hold periods
  SMOOTH_SETTLE: [0.25, 0.1, 0.25, 1] as const,
} as const;

/**
 * Kinetic mass spring config for aggressive physical slams:
 * Low mass and high stiffness ensures snappy 0.3s snap with satisfying physical bite.
 */
export const KINETIC_SPRING_CONFIG = {
  damping: 12,
  mass: 0.4,
  stiffness: 180,
  overshootClamping: false,
} as const;

export const SAAS_BEATS_T = [
  { id: 'HOOK', tStart: 0.00, tEnd: 0.25 },
  { id: 'PROOF', tStart: 0.25, tEnd: 0.50 },
  { id: 'ECOSYSTEM', tStart: 0.50, tEnd: 0.825 },
  { id: 'OUTRO', tStart: 0.825, tEnd: 1.00 },
] as const;

export const tToFrames = (t: number, durationInFrames: number): number => {
  return Math.round(t * durationInFrames);
};

export type BeatRenderMode = 'montage' | 'flight';
export type RenderMode = BeatRenderMode;

export const BEAT_RENDER_MODE: Record<typeof SAAS_BEATS_T[number]['id'], RenderMode> = {
  HOOK: 'montage',      // 2.5D Centered Hard-Cut
  PROOF: 'montage',     // 2.5D Centered Hard-Cut
  ECOSYSTEM: 'montage', // 2.5D Centered Hard-Cut (Change to 'flight' for 3D tours)
  OUTRO: 'montage',     // 2.5D Centered Hard-Cut
};

/**
 * Evaluates the 85% Agency Bezier Snap curve at progress t (0 to 1)
 */
export const bezierSnapEase = (t: number): number => {
  return solveCubicBezier(
    AGENCY_MOTION.BEZIER_SNAP[0],
    AGENCY_MOTION.BEZIER_SNAP[1],
    AGENCY_MOTION.BEZIER_SNAP[2],
    AGENCY_MOTION.BEZIER_SNAP[3],
    t
  );
};

/**
 * Evaluates the High-Speed Whip Pan curve at progress t (0 to 1)
 */
export const whipPanEase = (t: number): number => {
  return solveCubicBezier(
    AGENCY_MOTION.WHIP_PAN[0],
    AGENCY_MOTION.WHIP_PAN[1],
    AGENCY_MOTION.WHIP_PAN[2],
    AGENCY_MOTION.WHIP_PAN[3],
    t
  );
};

/**
 * Evaluates Exponential Ease Out at progress t (0 to 1)
 */
export const easeOutExpo = (t: number): number => {
  return solveCubicBezier(
    AGENCY_MOTION.EASE_OUT_EXPO[0],
    AGENCY_MOTION.EASE_OUT_EXPO[1],
    AGENCY_MOTION.EASE_OUT_EXPO[2],
    AGENCY_MOTION.EASE_OUT_EXPO[3],
    t
  );
};
