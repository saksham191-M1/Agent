import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadDMSans} from '@remotion/google-fonts/DMSans';
import {loadFont as loadOutfit} from '@remotion/google-fonts/Outfit';
import {loadFont as loadSpaceGrotesk} from '@remotion/google-fonts/SpaceGrotesk';
import {loadFont as loadNotoSans} from '@remotion/google-fonts/NotoSans';

const googleFonts: Record<string, () => {fontFamily: string}> = {
  inter: loadInter,
  'dm sans': loadDMSans,
  outfit: loadOutfit,
  'space grotesk': loadSpaceGrotesk,
  'noto sans': loadNotoSans,
};

const localFiles: Record<string, [string, string]> = {
  'dm sans': ['DM Sans', 'DMSans.ttf'],
  inter: ['Inter', 'Inter.ttf'],
  outfit: ['Outfit', 'Outfit.ttf'],
  'space grotesk': ['Space Grotesk', 'SpaceGrotesk.ttf'],
  'noto sans': ['Noto Sans', 'NotoSans.ttf'],
  'noto sans devanagari': ['Noto Sans Devanagari', 'NotoSansDevanagari.ttf'],
};

const loaded = new Set<string>();

export const loadFontForBrand = (requested: string): string => {
  const key = requested.toLowerCase().trim();

  // 1. Try @remotion/google-fonts loader first
  if (googleFonts[key] && !loaded.has(key)) {
    try {
      loaded.add(key);
      const res = googleFonts[key]();
      return res.fontFamily;
    } catch {
      // Fall through to local font face
    }
  }

  // 2. Fall back to local TTF assets
  const [family, file] = localFiles[key] ?? localFiles['noto sans'];
  if (typeof document !== 'undefined' && !loaded.has(family)) {
    loaded.add(family);
    const handle = delayRender(`Loading local font ${family}`);
    const face = new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, {weight: '100 900'});
    document.fonts.add(face);
    face.load().then(() => continueRender(handle)).catch(cancelRender);
  }
  return family;
};
