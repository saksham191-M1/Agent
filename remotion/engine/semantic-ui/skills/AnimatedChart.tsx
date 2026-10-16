import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import type {ChartSkillNode} from '../types';
import type {Tokens} from '../../types';
import {SpecularSheen} from '../VectorRenderer';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const AnimatedChartView: React.FC<{
  node: ChartSkillNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const accent = node.accentColor || tokens.colors.accent;
  const data = node.data && node.data.length > 0 ? node.data : [
    {label: 'Mon', value: 45},
    {label: 'Tue', value: 80},
    {label: 'Wed', value: 65},
    {label: 'Thu', value: 110},
    {label: 'Fri', value: 145},
  ];

  const maxValue = Math.max(...data.map((d) => d.value), 1);
  const chartHeight = 180;
  const chartWidth = 520;

  // Staggered spring entrance for each bar
  return (
    <div
      style={{
        width: 600,
        padding: '24px 28px',
        borderRadius: 24,
        background: 'linear-gradient(135deg, rgba(22, 26, 38, 0.94) 0%, rgba(12, 14, 22, 0.96) 100%)',
        border: '1px solid rgba(255, 255, 255, 0.14)',
        boxShadow: '0 24px 60px rgba(0, 0, 0, 0.55)',
        backdropFilter: 'blur(20px)',
        filter: dofFilter,
        position: 'relative',
        overflow: 'hidden',
        fontFamily: SANS_FONT_STACK,
      }}
    >
      <SpecularSheen progress={sheenProgress} />

      {/* Header */}
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20}}>
        <div>
          <div style={{fontSize: 18, fontWeight: 700, color: tokens.colors.text}}>{node.title}</div>
          <div style={{fontSize: 13, color: tokens.colors.muted, marginTop: 4}}>Live telemetry</div>
        </div>
        <div
          style={{
            padding: '6px 12px',
            borderRadius: 8,
            backgroundColor: `${accent}22`,
            color: accent,
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          +{Math.round((data[data.length - 1].value / data[0].value - 1) * 100)}%
        </div>
      </div>

      {/* Chart Canvas */}
      {node.chartType === 'line' || node.chartType === 'area' ? (
        <div style={{height: chartHeight, position: 'relative'}}>
          <svg width="100%" height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{overflow: 'visible'}}>
            <defs>
              <linearGradient id={`chart-grad-${node.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={accent} stopOpacity={0.4} />
                <stop offset="100%" stopColor={accent} stopOpacity={0.0} />
              </linearGradient>
            </defs>

            {/* Smooth Curve */}
            {(() => {
              const step = chartWidth / (data.length - 1);
              const points = data.map((d, i) => ({
                x: i * step,
                y: chartHeight - (d.value / maxValue) * (chartHeight - 30) - 15,
              }));

              let pathD = `M ${points[0].x} ${points[0].y}`;
              for (let i = 0; i < points.length - 1; i++) {
                const p0 = points[i];
                const p1 = points[i + 1];
                const cpX = (p0.x + p1.x) / 2;
                pathD += ` C ${cpX} ${p0.y}, ${cpX} ${p1.y}, ${p1.x} ${p1.y}`;
              }

              const areaD = `${pathD} L ${points[points.length - 1].x} ${chartHeight} L ${points[0].x} ${chartHeight} Z`;

              return (
                <>
                  {node.chartType === 'area' && <path d={areaD} fill={`url(#chart-grad-${node.id})`} />}
                  <path d={pathD} fill="none" stroke={accent} strokeWidth={3.5} strokeLinecap="round" />
                  {points.map((p, idx) => {
                    const dotSpring = spring({
                      frame: frame - idx * 3,
                      fps,
                      config: {damping: 12, mass: 0.4},
                    });
                    return (
                      <circle
                        key={idx}
                        cx={p.x}
                        cy={p.y}
                        r={interpolate(dotSpring, [0, 1], [0, 5])}
                        fill="#FFFFFF"
                        stroke={accent}
                        strokeWidth={3}
                      />
                    );
                  })}
                </>
              );
            })()}
          </svg>
        </div>
      ) : (
        /* Bar Chart */
        <div style={{display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: chartHeight, gap: 12}}>
          {data.map((item, idx) => {
            const barSpring = spring({
              frame: frame - idx * 2.5,
              fps,
              config: {damping: 14, mass: 0.45},
            });
            const barH = (item.value / maxValue) * (chartHeight - 36);
            const animatedH = interpolate(barSpring, [0, 1], [0, barH]);

            return (
              <div key={idx} style={{flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                <span style={{fontSize: 11, color: tokens.colors.muted, marginBottom: 6, fontWeight: 600}}>
                  {Math.round(item.value)}
                </span>
                <div
                  style={{
                    width: '100%',
                    maxWidth: 42,
                    height: animatedH,
                    borderRadius: '8px 8px 4px 4px',
                    background: `linear-gradient(180deg, ${accent} 0%, ${accent}99 100%)`,
                    boxShadow: `0 4px 16px ${accent}44`,
                  }}
                />
                <span style={{fontSize: 12, color: tokens.colors.muted, marginTop: 8, fontWeight: 500}}>
                  {item.label}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
