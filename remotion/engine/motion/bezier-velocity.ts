/**
 * Cubic Bezier Solver (Newton-Raphson approximation)
 * Emulates After Effects velocity graph influence handles (75-85% influence).
 */
export function solveCubicBezier(p1x: number, p1y: number, p2x: number, p2y: number, t: number): number {
  if (t <= 0) return 0;
  if (t >= 1) return 1;

  // Find parameter 'u' such that bezierX(u) = t
  let u = t;
  for (let i = 0; i < 8; i++) {
    const currentT = 3 * (1 - u) * (1 - u) * u * p1x + 3 * (1 - u) * u * u * p2x + u * u * u;
    const derivative = 3 * (1 - u) * (1 - u) * p1x + 6 * (1 - u) * u * (p2x - p1x) + 3 * u * u * (1 - p2x);
    if (Math.abs(currentT - t) < 1e-5 || Math.abs(derivative) < 1e-5) break;
    u -= (currentT - t) / derivative;
    u = Math.max(0, Math.min(1, u));
  }

  // Calculate bezierY(u)
  return 3 * (1 - u) * (1 - u) * u * p1y + 3 * (1 - u) * u * u * p2y + u * u * u;
}

/**
 * Agency-tier speed graph bezier evaluator:
 * Instant acceleration with 85% braking influence for a crisp, tactile snap.
 * Equivalent to AE Speed Graph: Incoming 85% influence, Outgoing 85% influence.
 */
export const agencySnapEase = (t: number): number => {
  return solveCubicBezier(0.16, 1.0, 0.3, 1.0, t);
};

export const smoothBrakeEase = (t: number): number => {
  return solveCubicBezier(0.25, 0.1, 0.25, 1.0, t);
};

/**
 * Calculates curved spatial cursor path with click compression:
 * P0 -> start coordinate, P1 -> control arc point, P2 -> target coordinate.
 * When arriving at target (progress near click), produces a 2-frame scale compression impulse (1.0 -> 0.88 -> 1.0).
 */
export function solveSpatialCursorPath(
  p0: [number, number],
  p1: [number, number],
  p2: [number, number],
  progress: number,
  clickWindow = {start: 0.9, click: 0.95, end: 1.0}
): {x: number; y: number; scale: number; clickImpulse: boolean} {
  const t = Math.max(0, Math.min(1, progress));
  const easeT = agencySnapEase(t);

  // Quadratic Bezier interpolation
  const inv = 1 - easeT;
  const x = inv * inv * p0[0] + 2 * inv * easeT * p1[0] + easeT * easeT * p2[0];
  const y = inv * inv * p0[1] + 2 * inv * easeT * p1[1] + easeT * easeT * p2[1];

  // 2-frame scale compression on click
  let scale = 1.0;
  let clickImpulse = false;

  if (t >= clickWindow.start && t <= clickWindow.end) {
    clickImpulse = true;
    if (t < clickWindow.click) {
      // Compressing: 1.0 -> 0.88
      const clickRatio = (t - clickWindow.start) / (clickWindow.click - clickWindow.start);
      scale = 1.0 - clickRatio * 0.12;
    } else {
      // Rebounding: 0.88 -> 1.0
      const releaseRatio = (t - clickWindow.click) / (clickWindow.end - clickWindow.click);
      scale = 0.88 + releaseRatio * 0.12;
    }
  }

  return {x, y, scale, clickImpulse};
}
