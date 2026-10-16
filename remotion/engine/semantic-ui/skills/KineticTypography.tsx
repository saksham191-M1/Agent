import React from 'react';
import {spring, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import type {TypographySkillNode} from '../types';
import type {Tokens} from '../../types';

const SANS_FONT_STACK = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export const KineticTypographyView: React.FC<{
  node: TypographySkillNode;
  tokens: Tokens;
  dofFilter?: string;
}> = ({node, tokens, dofFilter}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const accent = tokens.colors.accent;
  const effect = node.effect || 'phrase_flash';

  if (effect === 'word_carousel') {
    const words = node.words && node.words.length > 0 ? node.words : ['Smarter.', 'Swift.', 'Autonomous.'];
    const intervalFrames = Math.max(15, Math.floor(1.2 * fps));
    const activeIdx = Math.min(words.length - 1, Math.floor(frame / intervalFrames));
    const localF = frame % intervalFrames;

    const wordSpring = spring({
      frame: localF,
      fps,
      config: {damping: 12, mass: 0.4},
    });

    const translateY = interpolate(wordSpring, [0, 1], [40, 0]);
    const opacity = interpolate(wordSpring, [0, 1], [0, 1]);
    const scale = interpolate(wordSpring, [0, 1], [0.88, 1]);

    return (
      <div
        style={{
          textAlign: 'center',
          fontFamily: SANS_FONT_STACK,
          filter: dofFilter,
        }}
      >
        {node.subtext && (
          <div style={{fontSize: 20, color: tokens.colors.muted, marginBottom: 12, fontWeight: 500}}>
            {node.subtext}
          </div>
        )}
        <div
          style={{
            fontSize: node.fontSize || 72,
            fontWeight: 850,
            letterSpacing: '-0.035em',
            color: tokens.colors.text,
            transform: `translateY(${translateY}px) scale(${scale})`,
            opacity,
          }}
        >
          <span style={{color: accent}}>{words[activeIdx]}</span>
        </div>
      </div>
    );
  }

  if (effect === 'typewriter') {
    const text = node.text || 'Our smartest model yet.';
    const charsPerFrame = 0.5; // 2 frames per character
    const revealedChars = Math.min(text.length, Math.floor(frame * charsPerFrame));
    const cursorVisible = Math.sin(frame * 0.25) > 0;

    return (
      <div
        style={{
          textAlign: 'center',
          fontFamily: SANS_FONT_STACK,
          filter: dofFilter,
        }}
      >
        <div
          style={{
            fontSize: node.fontSize || 64,
            fontWeight: 800,
            letterSpacing: '-0.03em',
            color: tokens.colors.text,
            display: 'inline-flex',
            alignItems: 'center',
          }}
        >
          <span>{text.slice(0, revealedChars)}</span>
          <span
            style={{
              width: 4,
              height: (node.fontSize || 64) * 0.85,
              backgroundColor: accent,
              marginLeft: 4,
              opacity: cursorVisible ? 1 : 0,
            }}
          />
        </div>
        {node.subtext && (
          <div style={{fontSize: 22, color: tokens.colors.muted, marginTop: 14, fontWeight: 500}}>
            {node.subtext}
          </div>
        )}
      </div>
    );
  }

  // phrase_flash
  const flashSpring = spring({
    frame,
    fps,
    config: {damping: 10, mass: 0.35, stiffness: 200},
  });
  const scale = interpolate(flashSpring, [0, 1], [0.8, 1]);
  const opacity = interpolate(flashSpring, [0, 1], [0, 1]);

  return (
    <div
      style={{
        textAlign: 'center',
        fontFamily: SANS_FONT_STACK,
        filter: dofFilter,
        transform: `scale(${scale})`,
        opacity,
      }}
    >
      <div
        style={{
          fontSize: node.fontSize || 80,
          fontWeight: 850,
          letterSpacing: '-0.04em',
          color: tokens.colors.text,
          lineHeight: 1.1,
        }}
      >
        {node.text || 'Think deeper. Think swift.'}
      </div>
      {node.subtext && (
        <div style={{fontSize: 24, color: tokens.colors.muted, marginTop: 18, fontWeight: 500}}>
          {node.subtext}
        </div>
      )}
    </div>
  );
};
