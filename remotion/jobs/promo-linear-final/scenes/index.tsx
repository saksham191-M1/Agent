import React from 'react';
import {Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import {evaluateCameraBeatsT, type CameraBeatT} from '../../../engine/stage/CameraFlight';
import {SAAS_BEATS_T, AGENCY_MOTION, KINETIC_SPRING_CONFIG, BEAT_RENDER_MODE} from '../../../engine/motion/physics';
import uiTreeData from '../ui_tree.json';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Proportional stagger delays (in t-space)
const SPRING_DELAY_T: Record<string, number> = {
  interactive_input: 0,      // Hero slams at t=0
  pill_tag: 0.005,
  metric_card: 0.01,
  asset_card: 0.015,
  bento_grid: 0.02,
};

// Generalized: Map any node type to its story beat
const NODE_BEAT_MAP: Record<string, typeof SAAS_BEATS_T[number]['id']> = {
  interactive_input: 'HOOK',
  pill_tag: 'HOOK',
  metric_card: 'PROOF',
  asset_card: 'PROOF',
  bento_grid: 'ECOSYSTEM',
};

const getSpringForNode = (node: VectorNode, t: number, fps: number, durationInFrames: number) => {
  const delayT = SPRING_DELAY_T[node.type] ?? 0.01;
  const delayFrames = delayT * durationInFrames;
  const frame = t * durationInFrames;

  return spring({
    frame: frame - delayFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
};

const CAMERA_BEATS_T: CameraBeatT[] = [
  {
    id: 'beat1_hero_terminal',
    tStart: 0.00,
    tEnd: 0.25,
    position: [0, 110, -380],
    target: [0, 110, 0],
    rotationDeg: [0, 0, 0],
    fov: 36,
    transitionT: 0.03,
    easing: 'snap',
  },
  {
    id: 'beat2_metric_telemetry',
    tStart: 0.25,
    tEnd: 0.50,
    position: [-450, -40, -320],
    target: [-480, -30, 120],
    rotationDeg: [2, -7, 0],
    fov: 39,
    transitionT: 0.02,
    easing: 'whip',
  },
  {
    id: 'beat3_bento_ecosystem',
    tStart: 0.50,
    tEnd: 0.825,
    position: [-80, -270, -240],
    target: [0, -290, 260],
    rotationDeg: [3, 2, 0],
    fov: 42,
    transitionT: 0.023,
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
    transitionT: 0.025,
    easing: 'snap',
  },
];

const AgencyScene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  const localFrame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const globalFrame = Math.round((scene?.start || 0) * fps) + localFrame;
  const t = globalFrame / durationInFrames;

  const tree = uiTreeData as UITree;
  const accent = tokens?.colors?.accent || '#3ECF8E';
  const bg = tokens?.colors?.background || '#08090C';

  const cam = evaluateCameraBeatsT(CAMERA_BEATS_T, t);
  const camX = cam.position[0];
  const camY = cam.position[1];
  const camZ = cam.position[2];
  const targetX = cam.target[0];
  const targetY = cam.target[1];
  const targetZ = cam.target[2];
  const rotX = cam.rotationDeg[0];
  const rotY = cam.rotationDeg[1];

  const beat = SAAS_BEATS_T.find((b) => t >= b.tStart && t < b.tEnd) ?? SAAS_BEATS_T[SAAS_BEATS_T.length - 1];
  const activeRenderMode = BEAT_RENDER_MODE[beat.id as keyof typeof BEAT_RENDER_MODE] ?? 'montage';
  const isFlightBeat = activeRenderMode === 'flight';

  const getSheenProgressForNode = (node: VectorNode, normT: number) => {
    if (node.type === 'interactive_input') {
      return interpolate(normT, [0.02, 0.07], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    }
    if (node.type === 'metric_card') {
      return interpolate(normT, [0.25, 0.31], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    }
    if (node.type === 'bento_grid') {
      return interpolate(normT, [0.50, 0.56], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    }
    return 0;
  };

  const ctaSpring = spring({
    frame: (t - 0.84) * durationInFrames,
    fps,
    config: KINETIC_SPRING_CONFIG,
  });
  const ctaOpacity = interpolate(ctaSpring, [0, 1], [0, 1]);
  const ctaY = interpolate(ctaSpring, [0, 1], [40, 0]);
  const ctaScale = interpolate(ctaSpring, [0, 1], [0.82, 1]);

  const lensPerspective = interpolate(
    t,
    [0.16, 0.21, 0.80, 0.86],
    [500, 1200, 1200, 2500],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.bezier(0.7, 0, 0.3, 1),
    }
  );

  const whipBlurPx = interpolate(
    t,
    [0.16, 0.19, 0.21, 0.40, 0.425, 0.45, 0.66, 0.69, 0.71],
    [0, 12, 0, 0, 12, 0, 0, 8, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.bezier(0.25, 1, 0.5, 1),
    }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        backgroundColor: bg,
        backgroundImage: `radial-gradient(circle at 50% 30%, ${accent}22, transparent 70%)`,
        overflow: 'hidden',
        perspective: `${lensPerspective}px`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transformStyle: 'preserve-3d',
          transform: isFlightBeat
            ? `translate3d(${-camX}px, ${camY}px, ${-(camZ + 700)}px) rotateX(${rotX * 2}deg) rotateY(${rotY * 2}deg)`
            : 'none',
          filter: isFlightBeat ? `blur(${whipBlurPx}px)` : 'none',
        }}
      >
        {tree.nodes.map((node) => {
          const [x, y, z] = node.position3D;

          const nodeBeatId = (node as any).beat ?? NODE_BEAT_MAP[node.type] ?? 'ECOSYSTEM';
          const nodeBeat = SAAS_BEATS_T.find((b) => b.id === nodeBeatId)!;
          const renderMode = BEAT_RENDER_MODE[nodeBeatId as keyof typeof BEAT_RENDER_MODE] ?? 'montage';
          const nodeProgress = interpolate(t, [nodeBeat.tStart, nodeBeat.tEnd], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const easedNode = Easing.bezier(...AGENCY_MOTION.BEZIER_SNAP)(nodeProgress);
          const isFocused = renderMode === 'flight'
            ? (beat.id === nodeBeatId || beat.id === 'OUTRO')
            : (beat.id === nodeBeatId);

          const nodeSpring = getSpringForNode(node, t, fps, durationInFrames);
          const enterScale = interpolate(nodeSpring, [0, 1], [0.88, 1]);
          let crossfadeOpacity = 0;
          if (renderMode === 'flight') {
            if (t < nodeBeat.tStart) {
              crossfadeOpacity = interpolate(t, [nodeBeat.tStart - 0.03, nodeBeat.tStart], [0, 0.35], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else if (isFocused) {
              crossfadeOpacity = interpolate(nodeProgress, [0, 0.15], [0.35, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else {
              crossfadeOpacity = interpolate(t, [nodeBeat.tEnd, nodeBeat.tEnd + 0.03], [1, 0.35], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            }
          } else {
            if (t < nodeBeat.tStart - 0.015 || t > nodeBeat.tEnd + 0.015) {
              crossfadeOpacity = 0;
            } else if (t < nodeBeat.tStart + 0.03) {
              crossfadeOpacity = interpolate(t, [nodeBeat.tStart - 0.01, nodeBeat.tStart + 0.03], [0, 1], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else if (t > nodeBeat.tEnd - 0.02) {
              crossfadeOpacity = interpolate(t, [nodeBeat.tEnd - 0.02, nodeBeat.tEnd + 0.01], [1, 0], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              });
            } else {
              crossfadeOpacity = 1;
            }
          }
          const crossfadeY = isFocused ? (1 - easedNode) * 18 : 10;
          const crossfadeBlur = isFocused ? 0 : 12;
          const enterOpacity = crossfadeOpacity;
          const sheenProgress = getSheenProgressForNode(node, t);

          let activeNode = node;

          if (node.type === 'interactive_input' && node.typedValue) {
            const fullText = node.typedValue;
            const contentProgress = interpolate(t, [0.20, 0.37], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const chars = Math.max(1, Math.round(contentProgress * fullText.length));
            activeNode = {
              ...node,
              typedValue: fullText.slice(0, chars),
            };
          }

          if (node.type === 'metric_card' && node.chartPoints) {
            const contentProgress = interpolate(t, [0.40, 0.60], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            const animatedPoints = node.chartPoints.map((val, idx) => {
              const startVal = 45 + idx * 5;
              const pointThreshold = idx / (node.chartPoints.length - 1);
              const ease = Math.min(1, Math.max(0, (contentProgress - pointThreshold * 0.4) / 0.6));
              return Math.round(startVal + (val - startVal) * ease);
            });

            activeNode = {
              ...node,
              chartPoints: animatedPoints,
            };
          }

          const flightTransform = `translate3d(calc(-50% + ${x}px), calc(-50% - ${y}px + ${crossfadeY}px), ${z}px) scale(${enterScale})`;

          let montageTransform = `translate(-50%, calc(-50% + ${crossfadeY}px)) scale(${isFocused ? enterScale : 0.95})`;
          if (node.type === 'pill_tag') {
            const heroNode = tree.nodes.find((n) => n.type === 'interactive_input');
            const heroBaseY = heroNode?.position3D[1] ?? 110;
            const pillOffsetY = y - heroBaseY;
            montageTransform = `translate(calc(-50% + ${x}px), calc(-50% - ${pillOffsetY}px + ${crossfadeY}px)) scale(${isFocused ? enterScale : 0.95})`;
          } else if (node.type === 'metric_card' || node.type === 'asset_card') {
            const hasDualProof = tree.nodes.some(
              (n) => n.id !== node.id && (NODE_BEAT_MAP[n.type] === 'PROOF' || (n as any).beat === 'PROOF')
            );
            if (hasDualProof) {
              const xOffset = x < 0 ? -210 : 210;
              montageTransform = `translate(calc(-50% + ${xOffset}px), calc(-50% + ${crossfadeY}px)) scale(${isFocused ? enterScale : 0.95})`;
            }
          }

          const finalTransform = renderMode === 'flight' ? flightTransform : montageTransform;

          return (
            <div
              key={node.id}
              style={{
                position: 'absolute',
                left: '50%',
                top: '50%',
                transform: finalTransform,
                opacity: enterOpacity,
                filter: `blur(${crossfadeBlur}px)`,
                pointerEvents: isFocused ? 'auto' : 'none',
                zIndex: isFocused ? 10 : 1,
                willChange: 'transform, opacity, filter',
                transformStyle: renderMode === 'flight' ? 'preserve-3d' : undefined,
              }}
            >
              <VectorRenderer
                node={activeNode}
                tokens={tokens}
                cameraPosition={renderMode === 'flight' ? [camX, camY, camZ] : undefined}
                cameraTarget={renderMode === 'flight' ? [targetX, targetY, targetZ] : undefined}
                sheenProgress={sheenProgress}
              />
            </div>
          );
        })}

        {/* Final Brand CTA Lockup */}
        {t >= 0.83 && (
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: isFlightBeat
                ? `translate3d(-50%, calc(-50% + 20px + ${ctaY}px), 240px) scale(${ctaScale})`
                : `translate(-50%, calc(-50% + ${ctaY}px)) scale(${ctaScale})`,
              opacity: ctaOpacity,
              transformStyle: 'preserve-3d',
              padding: '24px 36px',
              borderRadius: 24,
              background: 'linear-gradient(135deg, rgba(20,24,36,0.92) 0%, rgba(10,12,18,0.96) 100%)',
              border: `1px solid ${accent}66`,
              boxShadow: `0 24px 70px rgba(0,0,0,0.7), 0 0 30px ${accent}33`,
              backdropFilter: 'blur(24px)',
              display: 'flex',
              alignItems: 'center',
              gap: 28,
              fontFamily: SANS_FONT_STACK,
              zIndex: 100,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: 16,
                background: '#0a0a0f',
                border: '1px solid rgba(255,255,255,0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
              }}
            >
              <Img
                src={staticFile('jobs/promo-linear-final/assets/logo.png')}
                alt="Logo"
                style={{width: 48, height: 48, objectFit: 'contain'}}
              />
            </div>
            <div>
              <div style={{fontSize: 22, fontWeight: 800, color: '#fff', letterSpacing: '-0.02em'}}>
                LinearApp
              </div>
              <div style={{fontSize: 14, color: '#94a3b8', marginTop: 4}}>
                The issue tracking tool you will enjoy using.
              </div>
            </div>
            <div
              style={{
                padding: '12px 28px',
                borderRadius: 14,
                background: `linear-gradient(135deg, ${accent} 0%, ${tokens?.colors?.accentLight || accent} 100%)`,
                color: '#041315',
                fontSize: 15,
                fontWeight: 700,
                letterSpacing: '0.01em',
                boxShadow: `0 8px 24px ${accent}44`,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              Get Started →
            </div>
          </div>
        )}
      </div>

      {/* Cinematic Post-Processing Overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 9999,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'radial-gradient(circle at 50% 50%, transparent 40%, rgba(5,7,12,0.85) 120%)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            // eslint-disable-next-line @remotion/no-background-image
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
            opacity: 0.05,
            mixBlendMode: 'overlay',
          }}
        />
      </div>
    </div>
  );
};

export default AgencyScene;
