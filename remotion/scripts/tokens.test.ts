import {assertContrast, getContrast} from '../engine/tokens';

function testTokens() {
  console.log('Testing light & dark contrast assertion...');

  // Light theme: dark text on light surface
  const lightBg = '#FAFAFA';
  const darkText = '#0F172A';
  const lightRatio = getContrast(darkText, lightBg);
  console.log(`Light theme contrast: ${lightRatio.toFixed(2)}:1`);
  assertContrast(darkText, lightBg, 4.5);

  // Dark theme: light text on dark surface
  const darkBg = '#0B1020';
  const lightText = '#F8FAFC';
  const darkRatio = getContrast(lightText, darkBg);
  console.log(`Dark theme contrast: ${darkRatio.toFixed(2)}:1`);
  assertContrast(lightText, darkBg, 4.5);

  // Failing case should throw
  let threw = false;
  try {
    assertContrast('#FFFFFF', '#F0F0F0', 4.5);
  } catch {
    threw = true;
  }
  if (!threw) {
    throw new Error('assertContrast should fail for white on light grey');
  }

  console.log('✅ tokens contrast assertion tests passed!');
}

testTokens();
