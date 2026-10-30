import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {KINETIC_SPRING_CONFIG} from '../../../engine/motion/physics';
import brandData from '../brand.json';

const SANS = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const RaycastMotionScene: React.FC<SceneRendererProps> = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / durationInFrames; // 0.0 to 1.0 (12 seconds total)

  // ── Global Camera Dynamic Movement ──────────────────────────────────────────
  const cameraPush = interpolate(frame, [0, durationInFrames], [1, 1.08], {extrapolateRight: 'clamp'});

  // Ambient rotating glow
  const glowX = 50 + Math.sin(frame * 0.03) * 15;
  const glowY = 40 + Math.cos(frame * 0.02) * 12;

  // ── Beat 1: Hook Pill & Headline (0.00 - 0.22, 0s - 2.6s) ─────────────────
  const hookSpring = spring({
    frame,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const hookScale = interpolate(hookSpring, [0, 1], [0.82, 1]);
  const hookY = interpolate(hookSpring, [0, 1], [80, 0]);
  const hookExit = t > 0.18
    ? interpolate(t, [0.18, 0.22], [1, 0], {extrapolateRight: 'clamp'})
    : 1;

  // ── Beat 2: 3D Isometric Command Bar (0.22 - 0.50, 2.6s - 6.0s) ───────────
  const barEnter = spring({
    frame: frame - Math.round(0.22 * durationInFrames),
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const barExit = t > 0.46
    ? interpolate(t, [0.46, 0.50], [1, 0], {extrapolateRight: 'clamp'})
    : 1;

  // 3D Isometric Tilt angles
  const tiltX = interpolate(t, [0.22, 0.50], [22, 14], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tiltY = interpolate(t, [0.22, 0.50], [-18, -8], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Typewriter for command prompt
  const fullPrompt = 'Ask AI or launch extension...';
  const typeProgress = interpolate(t, [0.24, 0.38], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const typedCount = Math.round(typeProgress * fullPrompt.length);
  const currentPrompt = fullPrompt.slice(0, typedCount);
  const caretBlink = Math.floor(frame / 15) % 2 === 0 ? '|' : '';

  // Interactive Cursor in 3D
  const cursorProgress = interpolate(t, [0.36, 0.44], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const isClicked = t >= 0.44;
  const clickScale = isClicked
    ? interpolate(t, [0.44, 0.46, 0.50], [0.94, 0.98, 1.0], {extrapolateRight: 'clamp'})
    : 1.0;

  // ── Beat 3: Exploded 3D Bento Space (0.50 - 0.78, 6.0s - 9.4s) ─────────────
  const bentoEnter = spring({
    frame: frame - Math.round(0.50 * durationInFrames),
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const bentoExit = t > 0.74
    ? interpolate(t, [0.74, 0.78], [1, 0], {extrapolateRight: 'clamp'})
    : 1;

  // Kinetic camera orbit around 3D widgets
  const orbitY = interpolate(t, [0.50, 0.78], [15, -12], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const orbitX = interpolate(t, [0.50, 0.78], [18, 10], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // Live Velocity metric ticker: 0ms -> 12ms
  const msTicker = Math.round(
    interpolate(t, [0.52, 0.68], [0, 12], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
  );

  // ── Beat 4: High-Impact 3D Outro (0.78 - 1.00, 9.4s - 12.0s) ──────────────
  const outroEnter = spring({
    frame: frame - Math.round(0.78 * durationInFrames),
    fps,
    config: KINETIC_SPRING_CONFIG,
  });

  return (
    <div
      style={{
        width: 1080,
        height: 1920,
        position: 'relative',
        backgroundColor: '#0A0C10',
        overflow: 'hidden',
        fontFamily: SANS,
        perspective: 1200,
        transformStyle: 'preserve-3d',
      }}
    >
      {/* ── Dynamic Ambient Lighting ───────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          width: 900,
          height: 900,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${brandData.colors.accent}33 0%, transparent 65%)`,
          filter: 'blur(140px)',
          left: `${glowX}%`,
          top: `${glowY}%`,
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: 'radial-gradient(circle, #38BDF822 0%, transparent 70%)',
          filter: 'blur(160px)',
          right: '10%',
          bottom: '15%',
          pointerEvents: 'none',
        }}
      />

      {/* ── Perspective 3D Grid Plane ──────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          inset: '-20%',
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px',
          transform: `rotateX(60deg) translateY(${frame * 1.5}px)`,
          transformOrigin: '50% 60%',
          opacity: 0.6,
          pointerEvents: 'none',
        }}
      />

      {/* ── Main 3D Spatial Stage ──────────────────────────────────────────── */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `scale(${cameraPush})`,
          transformStyle: 'preserve-3d',
        }}
      >

        {/* ── BEAT 1: HOOK (0.00 - 0.22) ────────────────────────────────────── */}
        {t < 0.23 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `translateY(${hookY}px) scale(${hookScale})`,
              opacity: hookExit,
            }}
          >
            {/* Pill Tag */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 12,
                padding: '12px 28px',
                borderRadius: 40,
                background: 'rgba(255, 255, 255, 0.07)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: `0 16px 36px rgba(0, 0, 0, 0.4), 0 0 20px ${brandData.colors.accent}25`,
                color: '#FFFFFF',
                fontSize: 22,
                fontWeight: 700,
                letterSpacing: '-0.02em',
                marginBottom: 32,
              }}
            >
              <span style={{color: brandData.colors.accent}}>⚡</span>
              <span>Next-Gen Launcher</span>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: brandData.colors.accent,
                  boxShadow: `0 0 12px ${brandData.colors.accent}`,
                  marginLeft: 4,
                }}
              />
            </div>

            {/* Kinetic Title */}
            <div
              style={{
                fontSize: 68,
                fontWeight: 900,
                letterSpacing: '-0.05em',
                lineHeight: 1.05,
                textAlign: 'center',
                maxWidth: 900,
                color: '#FFFFFF',
              }}
            >
              SUPERCHARGED
              <br />
              <span
                style={{
                  background: `linear-gradient(135deg, #FFFFFF 30%, ${brandData.colors.accent} 100%)`,
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                PRODUCTIVITY
              </span>
            </div>
            <div
              style={{
                marginTop: 20,
                fontSize: 24,
                color: '#94A3B8',
                fontWeight: 500,
              }}
            >
              Control everything with hotkeys in milliseconds.
            </div>
          </div>
        )}

        {/* ── BEAT 2: 3D COMMAND BAR & TYPEWRITER (0.22 - 0.50) ─────────────── */}
        {t >= 0.21 && t < 0.51 && (
          <div
            style={{
              position: 'relative',
              width: 860,
              transform: `
                rotateX(${tiltX}deg)
                rotateY(${tiltY}deg)
                scale(${barEnter * clickScale})
              `,
              opacity: barEnter * barExit,
              transformStyle: 'preserve-3d',
              transition: 'transform 0.1s ease-out',
            }}
          >
            {/* 3D Glass Command Launcher Card */}
            <div
              style={{
                borderRadius: 32,
                background: 'linear-gradient(135deg, rgba(30, 35, 48, 0.92) 0%, rgba(18, 22, 30, 0.96) 100%)',
                backdropFilter: 'blur(36px)',
                border: isClicked
                  ? `2px solid ${brandData.colors.accent}`
                  : '1px solid rgba(255, 255, 255, 0.16)',
                boxShadow: isClicked
                  ? `0 35px 90px rgba(0, 0, 0, 0.7), 0 0 45px ${brandData.colors.accent}55`
                  : '0 30px 80px rgba(0, 0, 0, 0.6), 0 0 20px rgba(255, 255, 255, 0.05)',
                overflow: 'hidden',
                padding: '30px 36px',
              }}
            >
              {/* Top search input row */}
              <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
                <span style={{fontSize: 34, color: brandData.colors.accent}}>⌕</span>
                <div style={{fontSize: 30, fontWeight: 600, color: '#FFFFFF', flex: 1}}>
                  {currentPrompt}
                  <span style={{color: brandData.colors.accent, fontWeight: 700}}>{caretBlink}</span>
                </div>
                {/* ⌘K Badge */}
                <div
                  style={{
                    padding: '8px 16px',
                    borderRadius: 12,
                    background: 'rgba(255, 255, 255, 0.10)',
                    border: '1px solid rgba(255, 255, 255, 0.18)',
                    fontSize: 18,
                    fontWeight: 800,
                    color: '#E2E8F0',
                  }}
                >
                  ⌘K
                </div>
              </div>

              {/* Suggestions items list */}
              <div style={{marginTop: 30, display: 'flex', flexDirection: 'column', gap: 14}}>
                {[
                  {icon: '✨', title: 'Ask Raycast AI', sub: 'Generate, explain or edit text', active: true},
                  {icon: '📋', title: 'Clipboard History', sub: 'Instant access to past copies', active: false},
                  {icon: '🚀', title: 'Launch VS Code Project', sub: 'Open repo in 1 click', active: false},
                ].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 18,
                      padding: '16px 20px',
                      borderRadius: 18,
                      background: item.active && isClicked
                        ? `${brandData.colors.accent}25`
                        : item.active
                        ? 'rgba(255, 255, 255, 0.07)'
                        : 'transparent',
                      border: item.active && isClicked
                        ? `1.5px solid ${brandData.colors.accent}`
                        : '1px solid transparent',
                    }}
                  >
                    <span style={{fontSize: 26}}>{item.icon}</span>
                    <div style={{flex: 1}}>
                      <div style={{fontSize: 20, fontWeight: 700, color: '#FFFFFF'}}>{item.title}</div>
                      <div style={{fontSize: 14, color: '#94A3B8', marginTop: 2}}>{item.sub}</div>
                    </div>
                    {item.active && (
                      <span style={{fontSize: 14, color: brandData.colors.accent, fontWeight: 800}}>
                        {isClicked ? 'Running... ↵' : '↵ Enter'}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* 3D Floating Cursor */}
            <div
              style={{
                position: 'absolute',
                left: `${interpolate(cursorProgress, [0, 1], [85, 48])}%`,
                top: `${interpolate(cursorProgress, [0, 1], [90, 42])}%`,
                transform: 'translate(-50%, -50%)',
                pointerEvents: 'none',
                filter: 'drop-shadow(0 10px 15px rgba(0,0,0,0.8))',
              }}
            >
              <svg width="42" height="54" viewBox="0 0 46 60" fill="none">
                <path
                  d="M8 4L38 35L25 36L33 54L24 58L16 39L7 47L8 4Z"
                  fill="#FFFFFF"
                  stroke="#0A0C10"
                  strokeWidth="3.5"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
        )}

        {/* ── BEAT 3: EXPLODED 3D BENTO SPACE (0.50 - 0.78) ──────────────────── */}
        {t >= 0.49 && t < 0.79 && (
          <div
            style={{
              position: 'relative',
              width: 880,
              transform: `
                rotateX(${orbitX}deg)
                rotateY(${orbitY}deg)
                scale(${bentoEnter})
              `,
              opacity: bentoEnter * bentoExit,
              transformStyle: 'preserve-3d',
            }}
          >
            {/* Card 1: Top Floating Pill (translateZ: 140px) */}
            <div
              style={{
                position: 'absolute',
                top: -80,
                left: 40,
                padding: '16px 30px',
                borderRadius: 24,
                background: 'rgba(255, 99, 99, 0.18)',
                backdropFilter: 'blur(20px)',
                border: `1.5px solid ${brandData.colors.accent}`,
                boxShadow: `0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px ${brandData.colors.accent}40`,
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                transform: 'translateZ(140px)',
              }}
            >
              <span style={{fontSize: 24}}>🔥</span>
              <span style={{fontSize: 20, fontWeight: 800, color: '#FFFFFF'}}>Over 1,000+ Extensions</span>
            </div>

            {/* Card 2: Main Velocity Metric (Center, translateZ: 80px) */}
            <div
              style={{
                marginTop: 60,
                padding: '36px 42px',
                borderRadius: 36,
                background: 'linear-gradient(135deg, rgba(26, 32, 44, 0.94) 0%, rgba(14, 18, 24, 0.98) 100%)',
                backdropFilter: 'blur(40px)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 35px 85px rgba(0, 0, 0, 0.7)',
                transform: 'translateZ(80px)',
              }}
            >
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
                <div>
                  <div style={{fontSize: 18, color: '#94A3B8', fontWeight: 600}}>EXECUTION VELOCITY</div>
                  <div
                    style={{
                      fontSize: 88,
                      fontWeight: 900,
                      color: '#FFFFFF',
                      letterSpacing: '-0.06em',
                      lineHeight: 1,
                      marginTop: 10,
                    }}
                  >
                    {msTicker}
                    <span style={{color: brandData.colors.accent, fontSize: 44, marginLeft: 6}}>ms</span>
                  </div>
                </div>
                <div
                  style={{
                    padding: '8px 18px',
                    borderRadius: 16,
                    background: `${brandData.colors.accent}22`,
                    border: `1px solid ${brandData.colors.accent}66`,
                    color: brandData.colors.accent,
                    fontWeight: 800,
                    fontSize: 16,
                  }}
                >
                  ⚡ INSTANT
                </div>
              </div>

              {/* Progress speed bar */}
              <div
                style={{
                  marginTop: 28,
                  height: 10,
                  borderRadius: 5,
                  background: 'rgba(255, 255, 255, 0.1)',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    width: `${(msTicker / 12) * 100}%`,
                    height: '100%',
                    background: `linear-gradient(90deg, #FF8787 0%, ${brandData.colors.accent} 100%)`,
                    borderRadius: 5,
                    boxShadow: `0 0 16px ${brandData.colors.accent}`,
                  }}
                />
              </div>
            </div>

            {/* Card 3: Floating Subcard (Bottom Right, translateZ: 200px) */}
            <div
              style={{
                position: 'absolute',
                bottom: -60,
                right: 30,
                padding: '20px 32px',
                borderRadius: 28,
                background: 'rgba(22, 27, 38, 0.95)',
                backdropFilter: 'blur(30px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                transform: 'translateZ(200px)',
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 14,
                  background: brandData.colors.accent,
                  display: 'grid',
                  placeItems: 'center',
                  color: '#FFFFFF',
                  fontWeight: 900,
                  fontSize: 22,
                }}
              >
                ⌘
              </div>
              <div>
                <div style={{fontSize: 18, fontWeight: 800, color: '#FFFFFF'}}>Zero Context Switching</div>
                <div style={{fontSize: 13, color: '#94A3B8', marginTop: 2}}>Stay fully in flow</div>
              </div>
            </div>
          </div>
        )}

        {/* ── BEAT 4: HIGH-IMPACT 3D OUTRO (0.78 - 1.00) ────────────────────── */}
        {t >= 0.77 && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              transform: `scale(${outroEnter})`,
              opacity: outroEnter,
            }}
          >
            {/* Glowing Logo Emblem */}
            <div
              style={{
                width: 140,
                height: 140,
                borderRadius: 42,
                background: 'linear-gradient(135deg, rgba(30, 35, 48, 0.95) 0%, rgba(18, 22, 30, 0.98) 100%)',
                border: `2px solid ${brandData.colors.accent}`,
                boxShadow: `0 25px 60px rgba(0, 0, 0, 0.8), 0 0 50px ${brandData.colors.accent}66`,
                display: 'grid',
                placeItems: 'center',
                marginBottom: 36,
              }}
            >
              <span style={{fontSize: 64, color: brandData.colors.accent}}>⚡</span>
            </div>

            <div
              style={{
                fontSize: 64,
                fontWeight: 900,
                letterSpacing: '-0.05em',
                textAlign: 'center',
                color: '#FFFFFF',
              }}
            >
              RAYCAST
            </div>
            <div
              style={{
                fontSize: 24,
                color: '#94A3B8',
                fontWeight: 600,
                marginTop: 10,
              }}
            >
              Your shortcut to everything.
            </div>

            {/* Punchy CTA Button */}
            <div
              style={{
                marginTop: 48,
                padding: '22px 56px',
                borderRadius: 50,
                background: brandData.colors.accent,
                color: '#FFFFFF',
                fontSize: 26,
                fontWeight: 800,
                letterSpacing: '-0.02em',
                boxShadow: `0 20px 50px ${brandData.colors.accent}66, 0 0 25px ${brandData.colors.accent}`,
                display: 'flex',
                alignItems: 'center',
                gap: 14,
              }}
            >
              <span>Download Free</span>
              <span style={{fontSize: 24}}>→</span>
            </div>

            <div
              style={{
                marginTop: 24,
                fontSize: 18,
                color: '#64748B',
                fontWeight: 600,
                letterSpacing: '0.05em',
              }}
            >
              RAYCAST.COM
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default RaycastMotionScene;
