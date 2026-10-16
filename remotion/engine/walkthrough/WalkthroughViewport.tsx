import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Video} from 'remotion';
import type {WalkthroughConfig} from './types';
import {solveCurvedCursorPath, solveClickContactImpulse} from './motor-physics';

export interface WalkthroughViewportProps {
  config: WalkthroughConfig;
  brandAccentColor?: string;
}

export const WalkthroughViewport: React.FC<WalkthroughViewportProps> = ({config, brandAccentColor = '#ffffff'}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  // 1. Evaluate Dynamic 2D Auto-Zoom & Pan Track
  let currentZoom = 1.0;
  let currentCenter: [number, number] = [1920, 1080];

  const zoomKeyframes = config.cameraZoomTrack;
  for (let i = 0; i < zoomKeyframes.length; i++) {
    const kf = zoomKeyframes[i];
    if (frame >= kf.startFrame && frame <= kf.endFrame) {
      const prevKf = i > 0 ? zoomKeyframes[i - 1] : null;
      const startZoom = prevKf ? prevKf.zoomScale : 1.0;
      const startCenter = prevKf ? prevKf.center : [1920, 1080];

      const progress = interpolate(frame, [kf.startFrame, kf.endFrame], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      });

      // Continuous cubic easing
      const easedProgress = progress * progress * (3 - 2 * progress); // smoothstep cubic

      currentZoom = startZoom + (kf.zoomScale - startZoom) * easedProgress;
      currentCenter = [
        startCenter[0] + (kf.center[0] - startCenter[0]) * easedProgress,
        startCenter[1] + (kf.center[1] - startCenter[1]) * easedProgress,
      ];
      break;
    }
  }

  // Calculate 2D Pan offset to center the focal point in the viewport
  // Viewport center is (width/2, height/2). Scaled canvas translation:
  const scale = currentZoom;
  const transX = (width / 2 - currentCenter[0]) * scale;
  const transY = (height / 2 - currentCenter[1]) * scale;

  // 2. Evaluate Cursor Motor Track
  let cursorX = -100;
  let cursorY = -100;
  let cursorScale = 1.0;
  let rippleRadius = 0;
  let rippleOpacity = 0;
  let isCursorVisible = false;

  for (const action of config.cursorTrack) {
    if (frame >= action.startFrame && frame <= action.endFrame + 15) {
      isCursorVisible = true;
      const totalFrames = Math.max(1, action.endFrame - action.startFrame);
      const progress = Math.min(1, Math.max(0, (frame - action.startFrame) / totalFrames));

      const pos = solveCurvedCursorPath(action.from, action.to, progress, action.arcOffset || 30);
      cursorX = pos.x;
      cursorY = pos.y;

      if (action.clickFrame) {
        const impulse = solveClickContactImpulse(frame, action.clickFrame);
        cursorScale = impulse.scale;
        rippleRadius = impulse.rippleRadius;
        rippleOpacity = impulse.rippleOpacity;
      }
      break;
    }
  }

  // 3. Spotlight dimming when zoom > 1.3x
  const isZoomed = currentZoom > 1.3;

  return (
    <AbsoluteFill style={{backgroundColor: '#090a10', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      {/* Ambient Brand Glow behind window canvas */}
      <div
        style={{
          position: 'absolute',
          width: width * 0.88,
          height: height * 0.88,
          borderRadius: 24,
          boxShadow: `0 40px 120px -20px ${brandAccentColor}22`,
          pointerEvents: 'none',
        }}
      />

      {/* macOS-style Window Frame Wrapper (Neutral Graphite #16161A with 1px border) */}
      <div
        style={{
          position: 'relative',
          width: width * 0.92,
          height: height * 0.9,
          borderRadius: 24,
          overflow: 'hidden',
          backgroundColor: '#16161A',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          boxShadow: '0 30px 80px rgba(0, 0, 0, 0.6)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* macOS Window Titlebar / Chrome */}
        <div
          style={{
            height: 48,
            backgroundColor: 'rgba(22, 22, 26, 0.95)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
            display: 'flex',
            alignItems: 'center',
            padding: '0 20px',
            gap: 10,
            zIndex: 10,
          }}
        >
          {/* Traffic Light Window Controls */}
          <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ff5f56'}} />
          <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#ffbd2e'}} />
          <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#27c93f'}} />
        </div>

        {/* Dynamic 2D Zoom Canvas */}
        <div style={{flex: 1, position: 'relative', overflow: 'hidden', backgroundColor: '#0d0e15'}}>
          <div
            style={{
              width: '100%',
              height: '100%',
              transform: `translate3d(${transX}px, ${transY}px, 0) scale(${scale})`,
              transformOrigin: 'center center',
              willChange: 'transform',
            }}
          >
            {/* Screen Recording Stream */}
            {config.sourceRecording ? (
              <Video src={config.sourceRecording} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
            ) : (
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#12141f',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'rgba(255,255,255,0.4)',
                  fontSize: 24,
                }}
              >
                [4K Retina Lossless Recording Stream]
              </div>
            )}

            {/* Peripheral Dimming / Spotlight Mask */}
            {isZoomed && (
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  backgroundColor: 'rgba(0, 0, 0, 0.22)',
                  backdropFilter: 'blur(2px)',
                  maskImage: `radial-gradient(circle 350px at ${currentCenter[0]}px ${currentCenter[1]}px, transparent 0%, black 100%)`,
                  WebkitMaskImage: `radial-gradient(circle 350px at ${currentCenter[0]}px ${currentCenter[1]}px, transparent 0%, black 100%)`,
                  pointerEvents: 'none',
                }}
              />
            )}

            {/* Sub-Pixel Vector Cursor Rig */}
            {isCursorVisible && (
              <div
                style={{
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  transform: `translate3d(${cursorX}px, ${cursorY}px, 0) scale(${cursorScale})`,
                  transformOrigin: 'top left',
                  willChange: 'transform',
                  pointerEvents: 'none',
                  zIndex: 100,
                }}
              >
                {/* Expanding Click Ripple Ring */}
                {rippleRadius > 0 && (
                  <div
                    style={{
                      position: 'absolute',
                      left: -rippleRadius / 2 + 2,
                      top: -rippleRadius / 2 + 2,
                      width: rippleRadius,
                      height: rippleRadius,
                      borderRadius: '50%',
                      border: `2px solid ${brandAccentColor}`,
                      opacity: rippleOpacity,
                    }}
                  />
                )}

                {/* macOS Vector Pointer */}
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path
                    d="M3 3L10.07 20.97L12.58 13.58L19.97 11.07L3 3Z"
                    fill="black"
                    stroke="white"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            )}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
