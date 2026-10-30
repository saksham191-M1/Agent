import {interpolate} from 'remotion';
import type {TypewriterConfig} from './types';

export function getTypedText(
  frame: number,
  config?: TypewriterConfig | boolean,
  fallbackText: string = ''
): {text: string; cursor: string; isTyping: boolean} {
  if (config === false) {
    return {text: fallbackText, cursor: '', isTyping: false};
  }

  const resolved = typeof config === 'object' ? config : {};
  const targetText = resolved.text ?? fallbackText;
  const startFrame = resolved.startFrame ?? 14;
  const durationFrames = resolved.durationFrames ?? 24;
  const showCursor = resolved.showCursor ?? true;

  const charsTyped = Math.floor(
    interpolate(frame - startFrame, [0, durationFrames], [0, targetText.length], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );

  const text = targetText.slice(0, Math.max(0, charsTyped));
  const isTyping = frame >= startFrame && frame < startFrame + durationFrames + 30;
  const cursor = showCursor && frame >= startFrame && Math.floor(frame / 14) % 2 === 0 ? '|' : '';

  return {text, cursor, isTyping};
}
