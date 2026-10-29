import React from 'react';
import {interpolate} from 'remotion';
import type {CaptionWord, Tokens} from '../types';

export const Captions: React.FC<{tokens: Tokens; words: CaptionWord[]; sceneFrame: number; visible?: boolean}> = ({tokens, words, sceneFrame, visible = true}) => {
  if (!visible) return null;
  const isLight = Boolean(tokens.colors.background && tokens.colors.background.toLowerCase().startsWith('#f'));
  const pillBg = isLight ? 'rgba(255, 255, 255, 0.96)' : `${tokens.colors.background}d9`;
  const pillBorder = isLight ? '1px solid rgba(0, 0, 0, 0.12)' : `1px solid ${tokens.colors.hairline}`;
  const normalTextColor = isLight ? 'rgba(15, 23, 42, 1)' : tokens.colors.text;
  const highlightColor = tokens.colors.accent;

  return (
    <div style={{position: 'absolute', bottom: 64, left: tokens.safe, right: tokens.safe, display: 'flex', justifyContent: 'center', zIndex: 30}}>
      <div style={{padding: '14px 24px', borderRadius: 18, background: pillBg, border: pillBorder, maxWidth: 940, fontFamily: tokens.fontFamily, fontSize: 40, lineHeight: 1.15, textAlign: 'center', color: normalTextColor, boxShadow: isLight ? '0 12px 36px rgba(0,0,0,0.1)' : `0 8px 30px ${tokens.colors.background}80`}}>
        {words.map((item, index) => {
          const active = sceneFrame >= item.start && sceneFrame <= item.end;
          const revealed = interpolate(Math.max(0, Math.min(1, (sceneFrame - item.start) / 5)), [0, 1], [0, 1]);
          return (
            <span
              key={`${item.word}-${index}`}
              style={{
                display: 'inline-block',
                marginRight: 9,
                opacity: revealed,
                color: active ? highlightColor : normalTextColor,
                textShadow: active && !isLight ? `0 0 18px ${tokens.colors.accent}80` : 'none',
                fontWeight: active ? 800 : 500
              }}
            >
              {item.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
