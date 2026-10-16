import React from 'react';
import {useCurrentFrame, interpolate} from 'remotion';

interface CursorWaypoint {
  frame: number;
  x: number;
  y: number;
  click?: boolean;
}

interface SmartCursorProps {
  waypoints?: CursorWaypoint[];
  accentColor?: string;
}

export const SmartCursor: React.FC<SmartCursorProps> = ({
  waypoints = [
    {frame: 0, x: 200, y: 350},
    {frame: 35, x: 420, y: 220, click: true},
    {frame: 70, x: 680, y: 380, click: true},
  ],
  accentColor = '#4F46E5',
}) => {
  const frame = useCurrentFrame();

  if (!waypoints || waypoints.length === 0) return null;

  // Find surrounding waypoints based on current frame
  let currentX = waypoints[0].x;
  let currentY = waypoints[0].y;
  let isClicking = false;
  let clickAge = 999;

  for (let i = 0; i < waypoints.length - 1; i++) {
    const w0 = waypoints[i];
    const w1 = waypoints[i + 1];

    if (frame >= w0.frame && frame <= w1.frame) {
      const progress = interpolate(frame, [w0.frame, w1.frame], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });
      // Ease in-out cubic
      const ease = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
      currentX = w0.x + (w1.x - w0.x) * ease;
      currentY = w0.y + (w1.y - w0.y) * ease;
      break;
    } else if (frame > w1.frame) {
      currentX = w1.x;
      currentY = w1.y;
    }
  }

  // Check for click events near current frame
  for (const wp of waypoints) {
    if (wp.click && Math.abs(frame - wp.frame) <= 15) {
      const age = frame - wp.frame;
      if (age >= 0 && age < clickAge) {
        clickAge = age;
        isClicking = true;
      }
    }
  }

  // Click pulse animation
  const clickScale = isClicking ? interpolate(clickAge, [0, 3, 10], [1, 0.85, 1], {extrapolateRight: 'clamp'}) : 1;
  const rippleRadius = isClicking ? interpolate(clickAge, [0, 15], [0, 32], {extrapolateRight: 'clamp'}) : 0;
  const rippleOpacity = isClicking ? interpolate(clickAge, [0, 15], [0.8, 0], {extrapolateRight: 'clamp'}) : 0;

  return (
    <div
      style={{
        position: 'absolute',
        left: currentX,
        top: currentY,
        pointerEvents: 'none',
        zIndex: 100,
        transform: `scale(${clickScale})`,
        transformOrigin: 'top left',
      }}
    >
      {/* Click ripple wave */}
      {isClicking && rippleRadius > 0 && (
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: rippleRadius * 2,
            height: rippleRadius * 2,
            borderRadius: '50%',
            backgroundColor: `${accentColor}33`,
            border: `2px solid ${accentColor}`,
            transform: 'translate(-50%, -50%)',
            opacity: rippleOpacity,
          }}
        />
      )}

      {/* Modern Cursor SVG */}
      <svg
        width="26"
        height="26"
        viewBox="0 0 24 24"
        fill="none"
        style={{
          filter: 'drop-shadow(0 3px 6px rgba(0, 0, 0, 0.45))',
        }}
      >
        <path
          d="M3 3L10.07 20.97L13.58 13.58L20.97 10.07L3 3Z"
          fill="rgb(255, 255, 255)"
          stroke="#0A0E17"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
};
