import type React from 'react';

export type CaptionWord = {word: string; start: number; end: number};

export type BrandJson = {
  name: string;
  domain: string;
  tagline: string;
  description: string;
  products: string[];
  logo: {src: string | null; text: string; alt: string; source: string};
  colors: Record<string, string>;
  fonts: {display: {family: string; source: string}; body: {family: string; source: string}};
  imagery: Array<{src: string; alt: string; source: string}>;
  claims: Array<{id: string; label: string; value: string; sourceUrl: string}>;
  meta?: {
    paletteSource?: 'extracted' | 'override' | 'hash';
    [key: string]: unknown;
  };
};

export type SceneSpec = {
  id: string;
  start: number;
  duration: number;
  layout: string;
  headline: string;
  subline: string;
  caption?: string;
  captionWords?: CaptionWord[];
  visual: Record<string, unknown>;
  motion: {enter: string; idle: string; exit: string; cursorPath?: [number, number][]};
  vo?: string;
  sfx: Array<{t: number; type: string; gain?: number}>;
  transitionOut: string;
};

export type AdSpec = {
  brand: string;
  format: '9:16' | '1:1' | '16:9';
  fps: number;
  durationSec: number;
  bpm: number;
  palette?: {
    background: string;
    background2?: string;
    surface?: string;
    surfaceText?: string;
    text?: string;
    muted?: string;
    accent: string;
    accentLight?: string;
    secondary?: string;
    isLightTheme?: boolean;
  };
  mlMatch?: {
    category: string;
    score: number;
    template: string;
    author?: string;
    techTags?: string[];
    referenceUrl?: string;
    aesthetic?: Record<string, any>;
  };
  scenes: SceneSpec[];
  audio: {
    assetsRoot: string;
    voice: {provider: string; voiceId: string; model: string; clips: Record<string, string>};
    music: {file: string; mood: string; volume: number};
    room: {file: string; volume: number};
    sfxFiles: Record<string, string>;
    duck: number;
  };
};

export type Tokens = {
  name: string;
  domain: string;
  tagline: string;
  logo: BrandJson['logo'];
  colors: Record<string, string>;
  fontFamily: string;
  displayFontFamily: string;
  safe: number;
  width: number;
  height: number;
  radius: number;
};

export type SceneRendererProps = {scene: SceneSpec; tokens: Tokens};
export type SceneRenderer = React.FC<SceneRendererProps>;
