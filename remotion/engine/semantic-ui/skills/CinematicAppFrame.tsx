import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import type {CinematicAppFrameNode} from '../types';
import type {Tokens} from '../../types';
import {SpecularSheen} from '../VectorRenderer';
import {SmartCursor} from './SmartCursor';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const CinematicAppFrameView: React.FC<{
  node: CinematicAppFrameNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const accent = tokens.colors.accent;
  const appName = node.appName || 'CloudScale OS';
  const topbarTitle = node.topbarTitle || 'Overview';
  const sidebarItems = node.sidebarItems && node.sidebarItems.length > 0 ? node.sidebarItems : [
    {id: 'dash', label: 'Dashboard', active: true},
    {id: 'analytics', label: 'Analytics', active: false},
    {id: 'deployments', label: 'Deployments', active: false},
    {id: 'settings', label: 'Settings', active: false},
  ];

  // Window entrance spring
  const windowEntrance = spring({
    frame,
    fps,
    config: {damping: 14, mass: 0.7},
  });
  const windowScale = interpolate(windowEntrance, [0, 1], [0.94, 1]);
  const windowOpacity = interpolate(windowEntrance, [0, 1], [0, 1]);

  // Dynamic cursor coordinates across the frame
  const cursorWaypoints = [
    {frame: 0, x: 180, y: 140},
    {frame: 35, x: 85, y: 155, click: true}, // clicks second sidebar item
    {frame: 70, x: 420, y: 260, click: true}, // clicks main action card
  ];

  return (
    <div
      style={{
        width: 820,
        height: 520,
        borderRadius: 20,
        background: '#0D1117',
        border: '1px solid rgba(255, 255, 255, 0.14)',
        boxShadow: '0 30px 80px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'relative',
        filter: dofFilter,
        fontFamily: SANS_FONT_STACK,
        transform: `scale(${windowScale})`,
        opacity: windowOpacity,
      }}
    >
      <SpecularSheen progress={sheenProgress} />

      {/* Embedded Smart Cursor */}
      <SmartCursor waypoints={cursorWaypoints} accentColor={accent} />

      {/* Window Chrome / Topbar */}
      <div
        style={{
          height: 44,
          backgroundColor: '#161B22',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          justifyContent: 'space-between',
          userSelect: 'none',
        }}
      >
        {/* macOS Traffic Lights */}
        <div style={{display: 'flex', alignItems: 'center', gap: 8, width: 80}}>
          <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#FF5F56'}} />
          <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#FFBD2E'}} />
          <div style={{width: 12, height: 12, borderRadius: '50%', backgroundColor: '#27C93F'}} />
        </div>

        {/* Center Breadcrumb */}
        <div style={{display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: tokens.colors.muted}}>
          <span style={{fontWeight: 600, color: tokens.colors.text}}>{appName}</span>
          <span>/</span>
          <span>{topbarTitle}</span>
        </div>

        {/* Right Badge / Status */}
        <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
          {node.badgeText && (
            <div
              style={{
                fontSize: 11,
                padding: '3px 8px',
                borderRadius: 6,
                backgroundColor: `${accent}22`,
                color: accent,
                fontWeight: 600,
              }}
            >
              {node.badgeText}
            </div>
          )}
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: '50%',
              backgroundColor: `${accent}40`,
              border: `1px solid ${accent}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 10,
              fontWeight: 700,
              color: 'rgb(255, 255, 255)',
            }}
          >
            AI
          </div>
        </div>
      </div>

      {/* Main Body (Sidebar + Content Viewport) */}
      <div style={{display: 'flex', flex: 1, overflow: 'hidden'}}>
        {/* Left Sidebar */}
        <div
          style={{
            width: 170,
            backgroundColor: '#11151C',
            borderRight: '1px solid rgba(255, 255, 255, 0.06)',
            padding: '16px 10px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', flexDirection: 'column', gap: 4}}>
            {sidebarItems.map((item) => {
              const isActive = item.active || (frame > 35 && item.id === 'analytics');
              return (
                <div
                  key={item.id}
                  style={{
                    padding: '8px 12px',
                    borderRadius: 8,
                    fontSize: 13,
                    fontWeight: isActive ? 600 : 500,
                    color: isActive ? 'rgb(255, 255, 255)' : tokens.colors.muted,
                    backgroundColor: isActive ? `${accent}33` : 'transparent',
                    border: isActive ? `1px solid ${accent}55` : '1px solid transparent',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      backgroundColor: isActive ? accent : 'rgba(255, 255, 255, 0.2)',
                    }}
                  />
                  <span>{item.label}</span>
                </div>
              );
            })}
          </div>

          <div
            style={{
              padding: '10px 12px',
              borderRadius: 8,
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
              fontSize: 11,
              color: tokens.colors.muted,
            }}
          >
            <div style={{fontWeight: 600, color: tokens.colors.text, marginBottom: 2}}>Pro Tier</div>
            <div>Cluster: us-east-1</div>
          </div>
        </div>

        {/* Right Main Content */}
        <div
          style={{
            flex: 1,
            backgroundColor: '#0D1117',
            padding: 24,
            display: 'flex',
            flexDirection: 'column',
            gap: 16,
            overflow: 'hidden',
          }}
        >
          {/* Top Metric Strip */}
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12}}>
            {[
              {label: 'API Requests', value: '4.8M', change: '+28%'},
              {label: 'P99 Latency', value: '18ms', change: '-45%'},
              {label: 'Success Rate', value: '99.98%', change: '+0.2%'},
            ].map((stat, i) => (
              <div
                key={i}
                style={{
                  padding: '12px 14px',
                  borderRadius: 12,
                  backgroundColor: '#161B22',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div style={{fontSize: 11, color: tokens.colors.muted}}>{stat.label}</div>
                <div style={{fontSize: 18, fontWeight: 700, color: tokens.colors.text, marginTop: 4}}>
                  {stat.value}
                </div>
                <div style={{fontSize: 10, color: 'rgb(16, 185, 129)', marginTop: 2, fontWeight: 600}}>
                  {stat.change}
                </div>
              </div>
            ))}
          </div>

          {/* Interactive Chart Canvas Card */}
          <div
            style={{
              flex: 1,
              borderRadius: 14,
              backgroundColor: '#161B22',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              padding: 16,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
              <span style={{fontSize: 13, fontWeight: 600, color: tokens.colors.text}}>Global Throughput</span>
              <span style={{fontSize: 11, color: tokens.colors.muted}}>Live stream</span>
            </div>

            {/* SVG Wave */}
            <svg width="100%" height="110" viewBox="0 0 500 110" style={{overflow: 'visible'}}>
              <path
                d="M 0 80 Q 70 30, 140 60 T 280 40 T 420 20 T 500 15"
                fill="none"
                stroke={accent}
                strokeWidth="2.5"
              />
              <path
                d="M 0 80 Q 70 30, 140 60 T 280 40 T 420 20 T 500 15 L 500 110 L 0 110 Z"
                fill={`${accent}18`}
              />
            </svg>

            <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 10, color: tokens.colors.muted}}>
              <span>00:00</span>
              <span>06:00</span>
              <span>12:00</span>
              <span>18:00</span>
              <span>24:00</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
