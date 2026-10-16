import React from 'react';
import {Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {KINETIC_SPRING_CONFIG} from '../../../engine/motion/physics';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const _MOTION_SWELL_BEATS = [
  { id: 'HOOK', tStart: 0.00, tEnd: 0.20 },
  { id: 'PROMPT', tStart: 0.20, tEnd: 0.40 },
  { id: 'FLASH', tStart: 0.40, tEnd: 0.60 },
  { id: 'BENTO', tStart: 0.60, tEnd: 0.80 },
  { id: 'OUTRO', tStart: 0.80, tEnd: 1.00 },
] as const;

const MotionSwellScene: React.FC<SceneRendererProps> = ({scene, tokens: _tokens}) => {
  const localFrame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const globalFrame = Math.round((scene?.start || 0) * fps) + localFrame;
  const t = globalFrame / durationInFrames;

  // Beat 1: Hook (Pill Tag)
  const hookSpring = spring({
    frame: t * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const hookScale = interpolate(hookSpring, [0, 1], [0.85, 1]);
  const hookY = interpolate(hookSpring, [0, 1], [50, 0]);

  // Beat 2: Prompt (Interactive Bar)
  const promptSpring = spring({
    frame: (t - 0.20) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const promptScale = interpolate(promptSpring, [0, 1], [0.92, 1]);
  const promptY = interpolate(promptSpring, [0, 1], [40, 0]);

  // Dynamic typing for prompt bar
  const fullPrompt = 'Our smartest, fastest model yet';
  const typingProgress = interpolate(t, [0.22, 0.36], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const typedCount = Math.max(1, Math.round(typingProgress * fullPrompt.length));
  const currentTypedText = fullPrompt.slice(0, typedCount);
  const cursorBlink = Math.sin(localFrame * 0.3) > 0;

  // Beat 3: Flash Text (Kinetic Typography)
  const flashPart = t < 0.50 ? 1 : 2;
  const flash1Spring = spring({
    frame: (t - 0.40) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const flash2Spring = spring({
    frame: (t - 0.50) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });

  // Beat 4: Bento (Document Cards)
  const bentoSpring = spring({
    frame: (t - 0.60) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const bentoScale = interpolate(bentoSpring, [0, 1], [0.90, 1]);
  const bentoY = interpolate(bentoSpring, [0, 1], [40, 0]);

  // Beat 5: Outro (CTA Lockup)
  const outroSpring = spring({
    frame: (t - 0.80) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const outroScale = interpolate(outroSpring, [0, 1], [0.88, 1]);
  const outroY = interpolate(outroSpring, [0, 1], [40, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(at 50% 50%, #FFD1C1, #C7B9FF)',
        overflow: 'hidden',
        fontFamily: SANS_FONT_STACK,
      }}
    >
      {/* Subtle Grain Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.2) 0%, rgba(0,0,0,0.04) 100%)',
          pointerEvents: 'none',
        }}
      />

      {/* --- BEAT 1: HOOK (Pill Tag) --- */}
      {t >= 0.00 && t < 0.20 && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(-50%, calc(-50% + ${hookY}px)) scale(${hookScale})`,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            padding: '14px 28px',
            borderRadius: 50,
            background: 'rgba(255, 255, 255, 0.82)',
            backdropFilter: 'blur(24px)',
            border: '1px solid rgba(255, 255, 255, 0.95)',
            boxShadow: '0 20px 50px rgba(78, 62, 110, 0.15)',
            color: '#111827',
            fontSize: 18,
            fontWeight: 650,
            letterSpacing: '-0.01em',
          }}
        >
          {/* Sparkle Icon */}
          <span style={{fontSize: 20}}>✨</span>
          <span>GPT-5 Flagship model</span>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 10px #10B981',
              marginLeft: 4,
            }}
          />
        </div>
      )}

      {/* --- BEAT 2: PROMPT (Interactive Bar) --- */}
      {t >= 0.20 && t < 0.40 && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(-50%, calc(-50% + ${promptY}px)) scale(${promptScale})`,
            width: 780,
            borderRadius: 24,
            background: 'rgba(255, 255, 255, 0.88)',
            backdropFilter: 'blur(30px)',
            border: '1px solid rgba(255, 255, 255, 0.95)',
            boxShadow: '0 30px 80px rgba(78, 62, 110, 0.2)',
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 22px',
              borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
            }}
          >
            <div style={{display: 'flex', gap: 8}}>
              <span style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#FF5F56'}} />
              <span style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#FFBD2E'}} />
              <span style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#27C93F'}} />
            </div>
            <span style={{fontSize: 13, color: '#6B7280', fontWeight: 500}}>Anthropic Agent</span>
            <div style={{width: 40}} />
          </div>

          {/* Typing Area */}
          <div
            style={{
              padding: '24px 28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', alignItems: 'center', gap: 4, fontSize: 20, color: '#111827', fontWeight: 550}}>
              <span>{currentTypedText}</span>
              <span
                style={{
                  width: 2,
                  height: 24,
                  backgroundColor: '#000000',
                  opacity: cursorBlink ? 1 : 0,
                  marginLeft: 2,
                }}
              />
            </div>
            <div
              style={{
                padding: '10px 22px',
                borderRadius: 14,
                backgroundColor: '#000000',
                color: '#FFFFFF',
                fontSize: 14,
                fontWeight: 700,
                letterSpacing: '0.01em',
              }}
            >
              Generate →
            </div>
          </div>
        </div>
      )}

      {/* --- BEAT 3: FLASH TEXT (Kinetic Typography) --- */}
      {t >= 0.40 && t < 0.60 && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
          }}
        >
          {flashPart === 1 ? (
            <div
              style={{
                transform: `scale(${interpolate(flash1Spring, [0, 1], [0.85, 1])})`,
                fontSize: 84,
                fontWeight: 800,
                color: '#111827',
                letterSpacing: '-0.04em',
                textShadow: '0 10px 30px rgba(0,0,0,0.06)',
              }}
            >
              Think deeper.
            </div>
          ) : (
            <div
              style={{
                transform: `scale(${interpolate(flash2Spring, [0, 1], [0.88, 1])})`,
                fontSize: 92,
                fontWeight: 850,
                color: '#000000',
                letterSpacing: '-0.045em',
                textShadow: '0 15px 40px rgba(0,0,0,0.1)',
              }}
            >
              Think faster.
            </div>
          )}
        </div>
      )}

      {/* --- BEAT 4: BENTO (Document Intelligence Grid) --- */}
      {t >= 0.60 && t < 0.80 && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(-50%, calc(-50% + ${bentoY}px)) scale(${bentoScale})`,
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 300px)',
            gap: 24,
          }}
        >
          {[
            {
              format: 'PDF',
              badgeColor: '#EF4444',
              title: 'PDF Intelligence',
              desc: 'High-fidelity document layout parsing across 1,000+ pages.',
            },
            {
              format: 'XLSX',
              badgeColor: '#10B981',
              title: 'Spreadsheets',
              desc: 'Automated multi-sheet tabular audit and formula analysis.',
            },
            {
              format: 'DOC',
              badgeColor: '#3B82F6',
              title: 'Structured Docs',
              desc: 'Semantic entity extraction and recursive reference graph.',
            },
          ].map((item, idx) => {
            const cardSpring = spring({
              frame: (t - 0.60 - idx * 0.02) * durationInFrames,
              fps,
              config: KINETIC_SPRING_CONFIG,
            });
            const cScale = interpolate(cardSpring, [0, 1], [0.85, 1]);
            return (
              <div
                key={item.format}
                style={{
                  transform: `scale(${cScale})`,
                  padding: '28px 24px',
                  borderRadius: 24,
                  background: 'rgba(255, 255, 255, 0.85)',
                  backdropFilter: 'blur(24px)',
                  border: '1px solid rgba(255, 255, 255, 0.95)',
                  boxShadow: '0 20px 50px rgba(78, 62, 110, 0.14)',
                }}
              >
                <div
                  style={{
                    display: 'inline-block',
                    padding: '6px 14px',
                    borderRadius: 10,
                    backgroundColor: `${item.badgeColor}18`,
                    color: item.badgeColor,
                    fontSize: 14,
                    fontWeight: 800,
                    letterSpacing: '0.04em',
                  }}
                >
                  {item.format}
                </div>
                <div style={{fontSize: 22, fontWeight: 750, color: '#111827', marginTop: 16}}>
                  {item.title}
                </div>
                <div style={{fontSize: 14, color: '#6B7280', marginTop: 8, lineHeight: 1.5}}>
                  {item.desc}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* --- BEAT 5: OUTRO (Available Now CTA Lockup) --- */}
      {t >= 0.80 && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: `translate(-50%, calc(-50% + ${outroY}px)) scale(${outroScale})`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24,
          }}
        >
          {/* Brand Logo Card */}
          <div
            style={{
              padding: '24px 36px',
              borderRadius: 32,
              background: 'rgba(255, 255, 255, 0.9)',
              backdropFilter: 'blur(30px)',
              border: '1px solid rgba(255, 255, 255, 0.95)',
              boxShadow: '0 30px 80px rgba(78, 62, 110, 0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: 20,
            }}
          >
            <Img
              src={staticFile('jobs/motion-swell-clone/assets/logo.png')}
              alt="Logo"
              style={{width: 52, height: 52, borderRadius: 14}}
            />
            <div>
              <div style={{fontSize: 26, fontWeight: 800, color: '#111827', letterSpacing: '-0.02em'}}>Anthropic</div>
              <div style={{fontSize: 14, color: '#6B7280', fontWeight: 500}}>GPT-5 Flagship Model</div>
            </div>
          </div>

          {/* Dark Action Pill */}
          <div
            style={{
              padding: '16px 36px',
              borderRadius: 50,
              backgroundColor: '#000000',
              color: '#FFFFFF',
              fontSize: 18,
              fontWeight: 700,
              letterSpacing: '-0.01em',
              boxShadow: '0 16px 40px rgba(0, 0, 0, 0.25)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>Available now</span>
            <span style={{fontSize: 20}}>↗</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MotionSwellScene;
