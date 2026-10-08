import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

const files: Record<string, [string, string]> = {
  'dm sans': ['DM Sans', 'DMSans.ttf'],
  inter: ['Inter', 'Inter.ttf'],
  outfit: ['Outfit', 'Outfit.ttf'],
  'space grotesk': ['Space Grotesk', 'SpaceGrotesk.ttf'],
  'noto sans': ['Noto Sans', 'NotoSans.ttf'],
  'noto sans devanagari': ['Noto Sans Devanagari', 'NotoSansDevanagari.ttf'],
};
const loaded = new Set<string>();

export const loadFontForBrand = (requested: string): string => {
  const [family, file] = files[requested.toLowerCase()] ?? files['noto sans'];
  if (typeof document !== 'undefined' && !loaded.has(family)) {
    loaded.add(family);
    const handle = delayRender(`Loading local font ${family}`);
    const face = new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, {weight: '100 900'});
    document.fonts.add(face);
    face.load().then(() => continueRender(handle)).catch(cancelRender);
  }
  return family;
};
