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

function isLightColor(hex?: string): boolean {
  if (!hex || !hex.startsWith('#') || hex.length < 7) return false;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.55;
}

export const loadTokens = (brand: BrandJson, format: AdSpec['format'] = '9:16'): Tokens => {
  const size = format === '1:1' ? {width: 1080, height: 1080} : format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};
  const bg = brand.colors?.background || defaults.background;
  const light = isLightColor(bg);

  const themeOverrides = light ? {
    hairline: 'rgba(0, 0, 0, 0.12)',
    glass: 'rgba(255, 255, 255, 0.85)',
    surface: '#FFFFFF',
    surfaceText: brand.colors?.text || 'currentColor',
    surfaceMuted: brand.colors?.muted || 'currentColor',
    text: brand.colors?.text || 'currentColor',
    muted: brand.colors?.muted || 'currentColor',
  } : {};

  return {
    name: brand.name,
    domain: brand.domain,
    tagline: brand.tagline,
    logo: brand.logo,
    colors: {...defaults, ...themeOverrides, ...brand.colors},
    fontFamily: loadFontForBrand(brand.fonts.body.family),
    displayFontFamily: loadFontForBrand(brand.fonts.display.family),
    safe: Math.round(Math.min(size.width, size.height) * .067),
    width: size.width,
    height: size.height,
    radius: 26,
  };
};
