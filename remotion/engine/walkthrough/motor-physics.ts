/**
 * 5th-order Minimum-Jerk polynomial trajectory (Flash & Hogan, 1985).
 * Models biological human arm and hand trajectory minimizing total derivative jerk:
 * x(t) = X0 + (X1 - X0) * (10*(t/T)^3 - 15*(t/T)^4 + 6*(t/T)^5)
 */
export function minimumJerkPosition(x0: number, x1: number, t: number, T: number): number {
  if (t <= 0) return x0;
  if (t >= T) return x1;
  const s = t / T;
  const poly = 10 * Math.pow(s, 3) - 15 * Math.pow(s, 4) + 6 * Math.pow(s, 5);
  return x0 + (x1 - x0) * poly;
}

/**
 * Evaluates cursor position along a curved spatial Bézier arc with minimum-jerk easing.
 * Adds a perpendicular offset displacement (15px to 45px) to simulate natural human arc.
 */
export function solveCurvedCursorPath(
  from: [number, number],
  to: [number, number],
  progress: number,
  arcOffset = 30
): {x: number; y: number} {
  const t = Math.max(0, Math.min(1, progress));
  const s = minimumJerkPosition(0, 1, t, 1);

  // Compute direction and perpendicular unit vector
  const dx = to[0] - from[0];
  const dy = to[1] - from[1];
  const dist = Math.sqrt(dx * dx + dy * dy) || 1;
  const perpX = -dy / dist;
  const perpY = dx / dist;

  // Arc displacement peaks around s = 0.5 (sine hump)
  const arcHeight = Math.sin(s * Math.PI) * arcOffset;

  const baseX = from[0] + dx * s;
  const baseY = from[1] + dy * s;

  return {
    x: Math.round((baseX + perpX * arcHeight) * 100) / 100, // Sub-pixel precision
    y: Math.round((baseY + perpY * arcHeight) * 100) / 100,
  };
}

/**
 * Click Contact Impulse:
 * On contact frame:
 * - Scale down from 1.0 -> 0.86 over 2 frames.
 * - Emits expanding ripple ring.
 * - Rebounds to 1.0 over 3 frames.
 */
export function solveClickContactImpulse(
  currentFrame: number,
  clickFrame: number
): {scale: number; rippleRadius: number; rippleOpacity: number} {
  const diff = currentFrame - clickFrame;

  if (diff < -2 || diff > 16) {
    return {scale: 1.0, rippleRadius: 0, rippleOpacity: 0};
  }

  // 1. Scale compression impulse
  let scale = 1.0;
  if (diff >= -2 && diff <= 0) {
    // Compressing: 1.0 -> 0.86
    const ratio = (diff + 2) / 2;
    scale = 1.0 - ratio * 0.14;
  } else if (diff > 0 && diff <= 3) {
    // Rebounding: 0.86 -> 1.0
    const ratio = diff / 3;
    scale = 0.86 + ratio * 0.14;
  }

  // 2. Expanding ripple ring (0 -> 42px over 14 frames)
  let rippleRadius = 0;
  let rippleOpacity = 0;
  if (diff >= 0 && diff <= 14) {
    const rippleProgress = diff / 14;
    rippleRadius = rippleProgress * 44;
    rippleOpacity = (1 - rippleProgress) * 0.8;
  }

  return {
    scale: Math.round(scale * 100) / 100,
    rippleRadius: Math.round(rippleRadius * 10) / 10,
    rippleOpacity: Math.round(rippleOpacity * 100) / 100,
  };
}

/**
 * Simulates human typing intervals with randomized keystroke timing (65ms-90ms)
 * and a 140ms pause after punctuation marks.
 */
export function simulateHumanTypingTimeline(
  text: string,
  startFrame: number,
  fps = 60
): Array<{char: string; frame: number; textSoFar: string}> {
  const timeline: Array<{char: string; frame: number; textSoFar: string}> = [];
  let currentFrame = startFrame;

  const msToFrames = (ms: number) => Math.max(1, Math.round((ms / 1000) * fps));

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    timeline.push({
      char,
      frame: currentFrame,
      textSoFar: text.slice(0, i + 1),
    });

    // Keystroke interval: 65ms - 90ms
    const baseInterval = 65 + ((i * 17) % 25);
    currentFrame += msToFrames(baseInterval);

    // Pause after punctuation: 140ms
    if (['.', ',', '!', '?', ';', ':'].includes(char)) {
      currentFrame += msToFrames(140);
    }
  }

  return timeline;
}
