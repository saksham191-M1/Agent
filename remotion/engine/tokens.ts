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

function getContrast(hex1: string, hex2: string): number {
  const getLum = (hex: string) => {
    if (!hex.startsWith('#') || hex.length < 7) return 0.5;
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const a = [r, g, b].map(v => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)));
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
  };
  const l1 = getLum(hex1);
  const l2 = getLum(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function assertContrast(color: string, bg: string, minRatio: number = 4.5): void {
  const ratio = getContrast(color, bg);
  if (ratio < minRatio) {
    throw new Error(`Contrast check failed: ${color} on ${bg} gives ${ratio.toFixed(2)}:1 (minimum ${minRatio}:1 required)`);
  }
}

// Export for consumer scripts & tests
export {getContrast, assertContrast};

export const loadTokens = (brand: BrandJson, format: AdSpec['format'] = '9:16'): Tokens => {
  const size = format === '1:1' ? {width: 1080, height: 1080} : format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};
  const bg = brand.colors?.background || defaults.background;
  const light = isLightColor(bg);

  const themeOverrides = light ? {
    hairline: 'rgba(0, 0, 0, 0.12)',
    glass: 'rgba(255, 255, 255, 0.95)',
    surface: '#FFFFFF',
    surfaceText: 'rgba(15, 23, 42, 1)',
    surfaceMuted: 'rgba(71, 85, 105, 1)',
    text: 'rgba(15, 23, 42, 1)',
    muted: 'rgba(71, 85, 105, 1)',
  } : {};

  return {
    name: brand.name,
    domain: brand.domain,
    tagline: brand.tagline,
    logo: brand.logo,
    colors: {...defaults, ...brand.colors, ...themeOverrides},
    fontFamily: loadFontForBrand(brand.fonts.body.family),
    displayFontFamily: loadFontForBrand(brand.fonts.display.family),
    safe: Math.round(Math.min(size.width, size.height) * .067),
    width: size.width,
    height: size.height,
    radius: 26,
  };
};
