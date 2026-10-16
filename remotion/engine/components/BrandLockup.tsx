import React from 'react';
import {Img, staticFile} from 'remotion';
import type {Tokens} from '../types';

export const BrandLockup: React.FC<{tokens: Tokens; large?: boolean}> = ({tokens, large = false}) => (
  <div style={{display: 'inline-flex', alignItems: 'center', color: tokens.colors.accent, fontFamily: tokens.fontFamily, fontWeight: 800, letterSpacing: '-0.055em', fontSize: large ? 42 : 28}}>
    {tokens.logo.src ? <Img src={staticFile(tokens.logo.src)} alt={tokens.logo.alt} style={{display: 'block', maxWidth: large ? 240 : 150, maxHeight: large ? 64 : 42}} /> : <span>{tokens.logo.text}</span>}
  </div>
);
