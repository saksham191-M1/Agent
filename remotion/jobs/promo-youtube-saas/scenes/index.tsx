import React from 'react';
import {useCurrentFrame, useVideoConfig, spring, interpolate} from 'remotion';
import type {SceneRendererProps} from '../../../engine';

const SANS_FONT_STACK = 'YouTube Sans, Roboto, Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

const OFFICIAL_YOUTUBE_SVG = (
  <svg viewBox="0 0 28.57 20" style={{width: 64, height: 45, filter: 'drop-shadow(0 0 16px rgba(255, 0, 0, 0.45))'}}>
    <path
      d="M 27.9727 3.16 C 28.5 5.12 28.5 9.24 28.5 10 C 28.5 10.76 28.5 14.88 27.9727 16.84 C 27.6745 17.95 26.7961 18.83 25.6868 19.13 C 23.7273 19.66 14.285 19.66 14.285 19.66 C 14.285 19.66 4.8427 19.66 2.8832 19.13 C 1.7739 18.83 0.8955 17.95 0.5973 16.84 C 0.07 14.88 0.07 10.76 0.07 10 C 0.07 9.24 0.07 5.12 0.5973 3.16 C 0.8955 2.05 1.7739 1.17 2.8832 0.87 C 4.8427 0.34 14.285 0.34 14.285 0.34 C 14.285 0.34 23.7273 0.34 25.6868 0.87 C 26.7961 1.17 27.6745 2.05 27.9727 3.16 Z"
      fill="#FF0000"
    />
    <polygon points="11.425,14.285 18.855,10 11.425,5.715" fill="#FFFFFF" />
  </svg>
);

const YouTubeScene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const sceneId = scene?.id || 'scene_hook';
  const progress = frame / durationInFrames;

  // Spring entrance
  const enterSpring = spring({
    frame,
    fps,
    config: {damping: 14, stiffness: 120, mass: 0.8},
  });

  const accentColor = tokens?.colors?.accent || '#FF0000';
  const bgColor = tokens?.colors?.background || '#0F0F0F';

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        backgroundColor: bgColor,
        backgroundImage: `radial-gradient(circle at 50% 30%, ${accentColor}22 0%, transparent 65%), radial-gradient(circle at 80% 80%, #1F1F1F 0%, ${bgColor} 100%)`,
        overflow: 'hidden',
        fontFamily: SANS_FONT_STACK,
        color: '#F1F1F1',
      }}
    >
      {/* Background Tech Grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `linear-gradient(to right, rgba(255, 255, 255, 0.035) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.035) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
          opacity: 0.7,
          pointerEvents: 'none',
        }}
      />

      {/* Floating Ambient Brand Glow */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          backgroundColor: accentColor,
          filter: 'blur(180px)',
          opacity: 0.15,
          pointerEvents: 'none',
          top: '25%',
          left: '30%',
          transform: `scale(${interpolate(progress, [0, 1], [0.9, 1.1])})`,
        }}
      />

      {/* ============================================================== */}
      {/* SCENE 1: THE HOOK (0.00s - 2.00s) */}
      {/* ============================================================== */}
      {sceneId === 'scene_hook' && (
        <div
          style={{
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.92, 1])}) translateY(${interpolate(enterSpring, [0, 1], [24, 0])}px)`,
            opacity: interpolate(enterSpring, [0, 1], [0, 1]),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 24,
            zIndex: 10,
            maxWidth: 1200,
            padding: '0 40px',
          }}
        >
          {/* Brand Kicker Lockup */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 12,
              padding: '8px 20px',
              borderRadius: 30,
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 0, 0, 0.35)',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)',
            }}
          >
            {OFFICIAL_YOUTUBE_SVG}
            <span style={{fontSize: 26, fontWeight: 700, letterSpacing: '0.05em', color: '#FFFFFF'}}>
              YouTube Studio
            </span>
            <span
              style={{
                fontSize: 14,
                padding: '3px 8px',
                borderRadius: 6,
                background: '#FF0000',
                color: '#FFF',
                fontWeight: 800,
                textTransform: 'uppercase',
              }}
            >
              PRO
            </span>
          </div>

          {/* Kinetic Headline */}
          <h1
            style={{
              fontSize: 68,
              fontWeight: 800,
              lineHeight: 1.15,
              margin: 0,
              background: 'linear-gradient(180deg, #FFFFFF 0%, #D4D4D4 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '-0.02em',
            }}
          >
            Stop guessing why videos stall.
          </h1>

          {/* Subline Tagline */}
          <p
            style={{
              fontSize: 28,
              color: '#AAAAAA',
              margin: 0,
              maxWidth: 780,
              lineHeight: 1.4,
              fontWeight: 500,
            }}
          >
            Real-time algorithmic retention telemetry for world-class creators.
          </p>
        </div>
      )}

      {/* ============================================================== */}
      {/* SCENE 2: CORE FEATURE TELEMETRY (2.00s - 7.00s) */}
      {/* ============================================================== */}
      {sceneId === 'scene_feature' && (
        <div
          style={{
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.94, 1])})`,
            opacity: interpolate(enterSpring, [0, 1], [0, 1]),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 20,
            zIndex: 10,
            width: '90%',
            maxWidth: 1300,
          }}
        >
          {/* Browser / Dashboard Frame */}
          <div
            style={{
              width: '100%',
              borderRadius: 16,
              background: '#1A1A1A',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 24px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(255, 0, 0, 0.15)',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            {/* Window Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 24px',
                background: '#141414',
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{display: 'flex', alignItems: 'center', gap: 14}}>
                <div style={{display: 'flex', gap: 6}}>
                  <div style={{width: 12, height: 12, borderRadius: '50%', background: '#FF5F56'}} />
                  <div style={{width: 12, height: 12, borderRadius: '50%', background: '#FFBD2E'}} />
                  <div style={{width: 12, height: 12, borderRadius: '50%', background: '#27C93F'}} />
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: 8, marginLeft: 12}}>
                  {OFFICIAL_YOUTUBE_SVG}
                  <span style={{fontSize: 16, fontWeight: 700, color: '#F1F1F1'}}>studio.youtube.com/analytics</span>
                </div>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '4px 12px',
                  borderRadius: 20,
                  background: 'rgba(255, 0, 0, 0.15)',
                  border: '1px solid rgba(255, 0, 0, 0.4)',
                  fontSize: 13,
                  fontWeight: 700,
                  color: '#FF4E45',
                }}
              >
                ● LIVE AUDIENCE RETENTION
              </div>
            </div>

            {/* Dashboard Body */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1.7fr 1fr',
                gap: 24,
                padding: 28,
              }}
            >
              {/* Left Column: Retention Curve */}
              <div
                style={{
                  background: '#212121',
                  borderRadius: 12,
                  padding: 24,
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                }}
              >
                <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                  <div>
                    <h3 style={{margin: 0, fontSize: 20, fontWeight: 700}}>Audience Retention Velocity</h3>
                    <p style={{margin: '4px 0 0', fontSize: 13, color: '#AAAAAA'}}>Second-by-second drop-off curve</p>
                  </div>
                  <div
                    style={{
                      background: 'rgba(46, 204, 113, 0.15)',
                      color: '#2ECC71',
                      padding: '4px 10px',
                      borderRadius: 6,
                      fontSize: 13,
                      fontWeight: 800,
                    }}
                  >
                    +34% Algorithmic Lift
                  </div>
                </div>

                {/* Animated Retention Graph */}
                <div style={{position: 'relative', width: '100%', height: 180}}>
                  <svg viewBox="0 0 500 180" style={{width: '100%', height: '100%', overflow: 'visible'}}>
                    <defs>
                      <linearGradient id="curveGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#FF0000" stopOpacity="0.5" />
                        <stop offset="100%" stopColor="#FF0000" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>
                    {/* Area fill */}
                    <path
                      d="M 20 20 Q 120 40 220 50 T 480 70 L 480 160 L 20 160 Z"
                      fill="url(#curveGrad)"
                    />
                    {/* Stroke line */}
                    <path
                      d="M 20 20 Q 120 40 220 50 T 480 70"
                      fill="none"
                      stroke="#FF0000"
                      strokeWidth="4"
                      strokeDasharray="600"
                      strokeDashoffset={interpolate(progress, [0, 0.8], [600, 0], {extrapolateRight: 'clamp'})}
                    />
                    {/* Data Points */}
                    <circle cx="20" cy="20" r="5" fill="#FFFFFF" stroke="#FF0000" strokeWidth="2" />
                    <circle cx="220" cy="50" r="5" fill="#FFFFFF" stroke="#FF0000" strokeWidth="2" />
                    <circle cx="480" cy="70" r="5" fill="#FFFFFF" stroke="#FF0000" strokeWidth="2" />
                  </svg>
                  {/* Axis labels */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: 12,
                      color: '#717171',
                      marginTop: 8,
                    }}
                  >
                    <span>0:00 (100%)</span>
                    <span>1:30 (84%)</span>
                    <span>3:00 (78%)</span>
                    <span>6:00 (72%)</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Telemetry Bento */}
              <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
                <div
                  style={{
                    background: '#212121',
                    borderRadius: 12,
                    padding: 18,
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                  }}
                >
                  <span style={{fontSize: 13, color: '#AAAAAA', fontWeight: 600}}>Impressions Click-Through Rate</span>
                  <div style={{fontSize: 32, fontWeight: 800, color: '#FFFFFF', marginTop: 4}}>
                    14.8% <span style={{fontSize: 14, color: '#2ECC71', fontWeight: 700}}>▲ 4.2%</span>
                  </div>
                  <span style={{fontSize: 12, color: '#717171'}}>Variant B thumbnail active</span>
                </div>

                <div
                  style={{
                    background: '#212121',
                    borderRadius: 12,
                    padding: 18,
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                  }}
                >
                  <span style={{fontSize: 13, color: '#AAAAAA', fontWeight: 600}}>Average View Duration</span>
                  <div style={{fontSize: 32, fontWeight: 800, color: '#FFFFFF', marginTop: 4}}>
                    8m 42s <span style={{fontSize: 14, color: '#2ECC71', fontWeight: 700}}>▲ 1m 15s</span>
                  </div>
                  <span style={{fontSize: 12, color: '#717171'}}>Top 2% in category</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* SCENE 3: CTA & CONVERSION (7.00s - 10.00s) */}
      {/* ============================================================== */}
      {sceneId === 'scene_cta' && (
        <div
          style={{
            transform: `scale(${interpolate(enterSpring, [0, 1], [0.9, 1])})`,
            opacity: interpolate(enterSpring, [0, 1], [0, 1]),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 28,
            zIndex: 10,
            maxWidth: 1000,
            padding: '0 40px',
          }}
        >
          {/* Glowing Emblem */}
          <div
            style={{
              width: 96,
              height: 96,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(255, 0, 0, 0.25) 0%, rgba(255, 0, 0, 0.05) 70%)',
              border: '2px solid rgba(255, 0, 0, 0.5)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 50px rgba(255, 0, 0, 0.4)',
            }}
          >
            {OFFICIAL_YOUTUBE_SVG}
          </div>

          <h2
            style={{
              fontSize: 64,
              fontWeight: 800,
              lineHeight: 1.1,
              margin: 0,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
            }}
          >
            Broadcast Your Signal.
          </h2>

          <p
            style={{
              fontSize: 26,
              color: '#AAAAAA',
              margin: 0,
              maxWidth: 700,
              lineHeight: 1.4,
              fontWeight: 500,
            }}
          >
            Scale your creative craft into predictable, exponential growth.
          </p>

          {/* High-Converting CTA Button */}
          <div
            style={{
              marginTop: 12,
              padding: '18px 44px',
              borderRadius: 36,
              background: '#FF0000',
              color: '#FFFFFF',
              fontSize: 22,
              fontWeight: 800,
              letterSpacing: '0.02em',
              boxShadow: '0 8px 30px rgba(255, 0, 0, 0.45), 0 0 20px rgba(255, 0, 0, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <span>Open YouTube Studio</span>
            <span style={{fontSize: 24}}>→</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default YouTubeScene;
