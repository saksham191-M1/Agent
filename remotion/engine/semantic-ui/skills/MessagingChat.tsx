import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, interpolate, Img} from 'remotion';
import type {MessagingSkillNode} from '../types';
import type {Tokens} from '../../types';
import {SpecularSheen} from '../VectorRenderer';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const MessagingChatView: React.FC<{
  node: MessagingSkillNode;
  tokens: Tokens;
  sheenProgress?: number;
  dofFilter?: string;
}> = ({node, tokens, sheenProgress, dofFilter}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const accent = tokens.colors.accent;
  const messages = node.messages && node.messages.length > 0 ? node.messages : [
    {id: 'm1', sender: 'user' as const, text: 'Can you generate the Q3 financial report?', time: '10:42 AM'},
    {id: 'm2', sender: 'agent' as const, text: 'Analyzing database metrics and generating summary charts now.', time: '10:42 AM'},
    {id: 'm3', sender: 'agent' as const, text: 'Report generated! Revenue is up +42% YoY.', time: '10:43 AM'},
  ];

  const staggerFrames = Math.floor(0.4 * fps); // Stagger message entrances

  return (
    <div
      style={{
        width: 540,
        padding: '24px 26px',
        borderRadius: 24,
        background: 'linear-gradient(135deg, rgba(20, 24, 38, 0.95) 0%, rgba(12, 14, 24, 0.98) 100%)',
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

      {/* Chat Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: 16,
          marginBottom: 18,
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              backgroundColor: 'rgb(16, 185, 129)',
              boxShadow: '0 0 10px rgba(16, 185, 129, 0.6)',
            }}
          />
          <div>
            <div style={{fontSize: 15, fontWeight: 700, color: tokens.colors.text}}>Agentic Chat</div>
            <div style={{fontSize: 12, color: tokens.colors.muted}}>Active Workspace Session</div>
          </div>
        </div>
        <div
          style={{
            padding: '4px 10px',
            borderRadius: 12,
            backgroundColor: `${accent}22`,
            border: `1px solid ${accent}44`,
            fontSize: 11,
            fontWeight: 600,
            color: accent,
          }}
        >
          AI Verified
        </div>
      </div>

      {/* Messages Stream */}
      <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
        {messages.map((msg, idx) => {
          const delay = idx * staggerFrames;
          const msgSpring = spring({
            frame: frame - delay,
            fps,
            config: {damping: 14, mass: 0.5},
          });

          const translateY = interpolate(msgSpring, [0, 1], [25, 0]);
          const opacity = interpolate(msgSpring, [0, 1], [0, 1]);
          const isUser = msg.sender === 'user';
          const isSystem = msg.sender === 'system';

          if (isSystem) {
            return (
              <div
                key={msg.id || idx}
                style={{
                  alignSelf: 'center',
                  padding: '4px 14px',
                  borderRadius: 12,
                  backgroundColor: 'rgba(255,255,255,0.06)',
                  color: tokens.colors.muted,
                  fontSize: 12,
                  transform: `translateY(${translateY}px)`,
                  opacity,
                }}
              >
                {msg.text}
              </div>
            );
          }

          return (
            <div
              key={msg.id || idx}
              style={{
                display: 'flex',
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                alignItems: 'flex-start',
                gap: 10,
                transform: `translateY(${translateY}px)`,
                opacity,
              }}
            >
              {!isUser && (
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: `${accent}33`,
                    border: `1px solid ${accent}66`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: accent,
                    fontSize: 13,
                    fontWeight: 700,
                    flexShrink: 0,
                  }}
                >
                  {msg.avatar ? (
                    <Img src={msg.avatar} alt="Avatar" style={{width: '100%', height: '100%', borderRadius: '50%'}} />
                  ) : (
                    'AI'
                  )}
                </div>
              )}

              <div
                style={{
                  maxWidth: '78%',
                  padding: '12px 16px',
                  borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                  backgroundColor: isUser ? `${accent}ee` : 'rgba(255, 255, 255, 0.08)',
                  color: isUser ? 'rgb(255, 255, 255)' : tokens.colors.text,
                  border: isUser ? 'none' : '1px solid rgba(255, 255, 255, 0.12)',
                  boxShadow: isUser ? `0 4px 16px ${accent}40` : '0 4px 14px rgba(0,0,0,0.2)',
                  fontSize: 14,
                  lineHeight: 1.45,
                }}
              >
                <div>{msg.text}</div>
                {msg.time && (
                  <div
                    style={{
                      fontSize: 10,
                      marginTop: 4,
                      textAlign: isUser ? 'right' : 'left',
                      color: isUser ? 'rgba(255,255,255,0.7)' : tokens.colors.muted,
                    }}
                  >
                    {msg.time}
                  </div>
                )}
              </div>

              {isUser && (
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: 'rgba(255,255,255,0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'rgb(255, 255, 255)',
                    fontSize: 12,
                    fontWeight: 700,
                    flexShrink: 0,
                  }}
                >
                  U
                </div>
              )}
            </div>
          );
        })}

        {/* Typing indicator */}
        {node.typingIndicator && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '10px 14px',
              borderRadius: 14,
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              alignSelf: 'flex-start',
              width: 50,
            }}
          >
            {[0, 1, 2].map((i) => {
              const bounce = Math.sin((frame + i * 5) * 0.25) * 3;
              return (
                <div
                  key={i}
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: accent,
                    transform: `translateY(${bounce}px)`,
                  }}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
