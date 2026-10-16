import {Easing} from 'remotion';
import {AGENCY_MOTION} from '../motion/physics';

export type CameraBeatT = {
  id: string;
  tStart: number; // 0.0 -> 1.0
  tEnd: number;   // 0.0 -> 1.0
  position: [number, number, number];
  target: [number, number, number];
  rotationDeg: [number, number, number];
  fov: number;
  transitionT: number; // duration of whip in t-space (e.g. 0.02 = 2% of video)
  easing: 'snap' | 'whip';
};

// Proportional beats - these work for ANY duration
export const CAMERA_BEATS_T: CameraBeatT[] = [
  {
    id: 'beat1_hero_terminal',
    tStart: 0.00,
    tEnd: 0.25,
    position: [0, 110, -380],
    target: [0, 110, 0],
    rotationDeg: [0, 0, 0],
    fov: 36,
    transitionT: 0.03, // 18f / 600f = 0.03
    easing: 'snap',
  },
  {
    id: 'beat2_metric_telemetry',
    tStart: 0.25,
    tEnd: 0.50,
    position: [-510, -80, -440],
    target: [-540, -80, 80],
    rotationDeg: [2, -7, 0],
    fov: 39,
    transitionT: 0.02, // 12f / 600f = 0.02
    easing: 'whip',
  },
  {
    id: 'beat3_bento_ecosystem',
    tStart: 0.50,
    tEnd: 0.825,
    position: [0, -300, -490],
    target: [0, -320, 140],
    rotationDeg: [3, 2, 0],
    fov: 42,
    transitionT: 0.023, // 14f / 600f
    easing: 'whip',
  },
  {
    id: 'beat4_wide_cta',
    tStart: 0.825,
    tEnd: 1.00,
    position: [0, -35, -880],
    target: [0, -40, 60],
    rotationDeg: [0, 0, 0],
    fov: 50,
    transitionT: 0.025, // 15f / 600f
    easing: 'snap',
  },
];

function getEasing(type: 'snap' | 'whip') {
  return type === 'whip'
    ? Easing.bezier(...AGENCY_MOTION.WHIP_PAN)
    : Easing.bezier(...AGENCY_MOTION.BEZIER_SNAP);
}

function lerp(a: number, b: number, p: number) {
  return a + (b - a) * p;
}

function lerpVec3(a: [number, number, number], b: [number, number, number], p: number): [number, number, number] {
  return [lerp(a[0], b[0], p), lerp(a[1], b[1], p), lerp(a[2], b[2], p)];
}

export function evaluateCameraBeatsT(beats: CameraBeatT[], t: number) {
  const clampedT = Math.max(0, Math.min(0.9999, t));
  let idx = beats.findIndex((b) => clampedT >= b.tStart && clampedT < b.tEnd);
  if (idx === -1) idx = beats.length - 1;

  const curr = beats[idx];
  const prev = idx > 0 ? beats[idx - 1] : curr;

  // If we are inside the whip transition window at the start of this beat
  const transitionEnd = curr.tStart + curr.transitionT;
  const isTransitioning = clampedT >= curr.tStart && clampedT < transitionEnd && idx > 0;

  if (isTransitioning) {
    const p = (clampedT - curr.tStart) / curr.transitionT; // 0 -> 1 inside whip
    const eased = getEasing(curr.easing)(p);
    return {
      position: lerpVec3(prev.position, curr.position, eased),
      target: lerpVec3(prev.target, curr.target, eased),
      rotationDeg: lerpVec3(prev.rotationDeg, curr.rotationDeg, eased),
      fov: lerp(prev.fov, curr.fov, eased),
      beatId: curr.id,
      isTransitioning: true,
    };
  }

  // Rock-solid hold - no interpolation
  return {
    position: curr.position,
    target: curr.target,
    rotationDeg: curr.rotationDeg,
    fov: curr.fov,
    beatId: curr.id,
    isTransitioning: false,
  };
}

// Backward compatibility: if called with globalFrame
export function evaluateCameraBeats(beats: any[], globalFrame: number, durationInFrames: number = 600) {
  const t = globalFrame / durationInFrames;
  // Auto-convert old absolute beats to T on the fly
  const beatsT: CameraBeatT[] = beats.map((b) => ({
    ...b,
    tStart: b.tStart ?? b.startFrame / durationInFrames,
    tEnd: b.tEnd ?? b.endFrame / durationInFrames,
    transitionT: b.transitionT ?? (b.transitionFrames ?? 0) / durationInFrames,
  }));
  return evaluateCameraBeatsT(beatsT, t);
}
