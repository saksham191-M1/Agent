import type {AdSpec, BrandJson, Tokens} from './types';
import {loadFontForBrand} from './font-loader';

const defaults = {
  accent: '#6c5ce7',
  accentLight: '#b9b0ff',
  background: '#0b1020',
  background2: '#151b33',
  text: '#f7f8ff',
  muted: '#aab3c8',
  hairline: 'rgba(255,255,255,0.14)',
  glass: 'rgba(255,255,255,0.08)',
  surface: '#f7f8ff',
  surfaceText: '#172033',
  surfaceMuted: '#68748a',
};

export const loadTokens = (brand: BrandJson, format: AdSpec['format'] = '9:16'): Tokens => {
  const size = format === '1:1' ? {width: 1080, height: 1080} : format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};
  return {
  name: brand.name,
  domain: brand.domain,
  tagline: brand.tagline,
  logo: brand.logo,
  colors: {...defaults, ...brand.colors},
  fontFamily: loadFontForBrand(brand.fonts.body.family),
  displayFontFamily: loadFontForBrand(brand.fonts.display.family),
  safe: Math.round(Math.min(size.width, size.height) * .067),
  width: size.width,
  height: size.height,
  radius: 26,
  };
};
