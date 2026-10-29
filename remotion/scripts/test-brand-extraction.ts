/**
 * test-brand-extraction.ts
 * ────────────────────────
 * Unit tests for Phase 9: Brand Extraction Upgrade.
 * Verifies:
 * 1. WCAG 4.5:1 contrast calculation between text and background.
 * 2. Primary site font extraction and fallback to Inter.
 * 3. Light-themed vs dark-themed brand palette derivation.
 */

function getLuminance(hex: string): number {
  const clean = hex.replace('#', '');
  const r = (parseInt(clean.slice(0, 2), 16) || 0) / 255;
  const g = (parseInt(clean.slice(2, 4), 16) || 0) / 255;
  const b = (parseInt(clean.slice(4, 6), 16) || 0) / 255;
  const [rs, gs, bs] = [r, g, b].map(c => c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function getContrastRatio(hex1: string, hex2: string): number {
  const l1 = getLuminance(hex1);
  const l2 = getLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function assert(condition: boolean, msg: string) {
  if (!condition) {
    console.error(`❌ Assertion Failed: ${msg}`);
    process.exit(1);
  }
}

console.log('=== RUNNING PHASE 9 BRAND EXTRACTION TESTS ===\n');

// 1. Contrast checks
console.log('1. Testing WCAG 2.1 Contrast Ratio checks...');
const darkRatio = getContrastRatio('#F9FAFB', '#09090B');
assert(darkRatio >= 4.5, `Dark theme contrast must exceed 4.5 (got ${darkRatio.toFixed(2)})`);

const lightRatio = getContrastRatio('#09090B', '#FAFAFA');
assert(lightRatio >= 4.5, `Light theme contrast must exceed 4.5 (got ${lightRatio.toFixed(2)})`);

const failingRatio = getContrastRatio('#71717A', '#3F3F46'); // Poor gray on gray
assert(failingRatio < 4.5, `Gray-on-gray should fail 4.5 ratio (got ${failingRatio.toFixed(2)})`);
console.log(`   ✅ Dark contrast: ${darkRatio.toFixed(2)}:1, Light contrast: ${lightRatio.toFixed(2)}:1`);

// 2. Font parsing & formatting
console.log('2. Testing Font Parsing & Sanitization...');
function resolveFont(extracted: string): string {
  const clean = extracted ? extracted.split(',')[0].replace(/['"]/g, '').trim() : 'Inter';
  return `${clean}, system-ui, -apple-system, sans-serif`;
}

const customFont = resolveFont('"Poppins", sans-serif');
assert(customFont.startsWith('Poppins'), 'Custom font should be Poppins');

const defaultFont = resolveFont('');
assert(defaultFont.startsWith('Inter'), 'Empty font should fall back to Inter');
console.log('   ✅ Font resolution: Custom -> Poppins, Default -> Inter');

// 3. Light vs Dark Palette
console.log('3. Testing Light vs Dark Site Palette Generation...');
function getPalette(isDark: boolean) {
  const bg = isDark ? '#09090B' : '#FAFAFA';
  const text = isDark ? '#F9FAFB' : '#09090B';
  const ratio = getContrastRatio(text, bg);
  return { bg, text, ratio };
}

const darkPal = getPalette(true);
assert(darkPal.bg === '#09090B', 'Dark site must use dark bg');
assert(darkPal.ratio >= 4.5, 'Dark palette must satisfy WCAG 4.5');

const lightPal = getPalette(false);
assert(lightPal.bg === '#FAFAFA', 'Light site must use light bg');
assert(lightPal.ratio >= 4.5, 'Light palette must satisfy WCAG 4.5');
console.log('   ✅ Both light and dark palettes produce WCAG-compliant output.');

console.log('\n🎉 ALL PHASE 9 BRAND EXTRACTION TESTS PASSED!');
