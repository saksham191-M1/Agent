/**
 * test-primitives.ts
 * ──────────────────
 * Unit tests for Phase 6: Assembler and Composable Primitives.
 * Verifies:
 * 1. Storyboard Zod schema validator (spec-schema.ts)
 * 2. Primitives registry (all 9 primitives with schemas, defaults, and fallback)
 * 3. 3-scene and 7-scene storyboard fixtures validation and assembly
 * 4. Punctuation ban enforcement in Zod schema
 */

import fs from 'node:fs';
import path from 'node:path';
import { validateStoryboardSpec } from './spec-schema';
import { PRIMITIVE_REGISTRY } from '../engine/primitives';
import { assembleScenes } from './scene-assembler';
import type { BrandJson } from '../engine/types';

function assert(condition: boolean, msg: string) {
  if (!condition) {
    console.error(`❌ Assertion Failed: ${msg}`);
    process.exit(1);
  }
}

console.log('=== RUNNING PHASE 6 PRIMITIVES & ASSEMBLER TESTS ===\n');

// ──────────────────────────────────────────────────────────────────────────────
// Test 1: Primitives Registry Completeness
// ──────────────────────────────────────────────────────────────────────────────
console.log('1. Testing Primitives Registry...');
const expectedPrimitives = [
  'phone_frame',
  'browser_frame',
  'kinetic_headline',
  'metric_counter',
  'card_grid',
  'screenshot_pan',
  'logo_reveal',
  'feature_list',
  'quote_card',
];

for (const id of expectedPrimitives) {
  assert(Boolean(PRIMITIVE_REGISTRY[id]), `Primitive ${id} must be in PRIMITIVE_REGISTRY`);
  const def = PRIMITIVE_REGISTRY[id];
  assert(Boolean(def.schema), `Primitive ${id} must have a zod schema`);
  assert(Boolean(def.defaultProps), `Primitive ${id} must declare defaultProps`);
  assert(Boolean(def.component), `Primitive ${id} must have a React component`);
  assert(['full', 'left', 'right', 'overlay'].includes(def.slot), `Primitive ${id} must have valid slot`);
}
console.log('   ✅ All 9 primitives registered with valid schemas and slots.');

// ──────────────────────────────────────────────────────────────────────────────
// Test 2: Storyboard Schema Validation on 3-scene and 7-scene fixtures
// ──────────────────────────────────────────────────────────────────────────────
console.log('2. Testing 3-scene and 7-scene fixtures...');

const fixture3Scenes = {
  product_name: 'ShortAdApp',
  narrative_type: 'minimal_aesthetic_reveal',
  selected_template: 'Minimal Aesthetic Reveal',
  scene_count: 3,
  total_seconds: 12.0,
  music_mood: 'ambient_minimal',
  voice_style: 'calm_precise',
  scenes: [
    {
      scene_id: 1,
      duration_seconds: 4.0,
      layout: 'hero-type',
      voiceover: 'Simplicity redefined.',
      kinetic_text: 'PURE FOCUS',
      transition_out: 'carousel_glide',
    },
    {
      scene_id: 2,
      duration_seconds: 4.5,
      layout: 'split',
      voiceover: 'Everything you need, nothing you do not.',
      kinetic_text: 'ZERO DISTRACTION',
      transition_out: 'wipe',
    },
    {
      scene_id: 3,
      duration_seconds: 3.5,
      layout: 'cta',
      voiceover: 'Experience it today.',
      kinetic_text: 'TRY NOW',
      transition_out: 'carousel_glide',
    },
  ],
};

const valid3 = validateStoryboardSpec(fixture3Scenes);
assert(valid3.scenes.length === 3, '3-scene fixture must parse 3 scenes');
assert(valid3.total_seconds === 12.0, '3-scene fixture total duration must equal 12.0');
console.log('   ✅ 3-scene fixture passed validation.');

const fixture7Scenes = {
  product_name: 'EnterprisePlatform',
  narrative_type: 'technical_deep_dive',
  selected_template: 'Technical Deep Dive',
  scene_count: 7,
  total_seconds: 28.0,
  music_mood: 'high_energy_electronic',
  voice_style: 'confident_engineer',
  scenes: [
    { scene_id: 1, duration_seconds: 4.0, layout: 'hero-type', voiceover: 'Engineered for extreme performance.', kinetic_text: 'NEXT GEN CLOUD' },
    { scene_id: 2, duration_seconds: 4.0, layout: 'phone', voiceover: 'Real-time telemetry on the go.', kinetic_text: 'INSTANT METRICS' },
    { scene_id: 3, duration_seconds: 4.0, layout: 'browser', voiceover: 'Collaborative pipeline orchestrator.', kinetic_text: 'FULL CONTROL' },
    { scene_id: 4, duration_seconds: 4.0, layout: 'split', voiceover: 'Deploy multi-region clusters instantly.', kinetic_text: 'GLOBAL SCALE' },
    { scene_id: 5, duration_seconds: 4.0, layout: 'big-number', voiceover: 'Zero downtime guaranteed for mission critical ops.', kinetic_text: '99 POINT 99 UPTIME' },
    { scene_id: 6, duration_seconds: 4.0, layout: 'browser', voiceover: 'Seamless integration with existing developer toolchains.', kinetic_text: 'DEVELOPER FIRST' },
    { scene_id: 7, duration_seconds: 4.0, layout: 'cta', voiceover: 'Start deploying today.', kinetic_text: 'SHIP YOUR CODE' },
  ],
};

const valid7 = validateStoryboardSpec(fixture7Scenes);
assert(valid7.scenes.length === 7, '7-scene fixture must parse 7 scenes');
assert(valid7.total_seconds === 28.0, '7-scene fixture total duration must equal 28.0');
console.log('   ✅ 7-scene fixture passed validation.');

// ──────────────────────────────────────────────────────────────────────────────
// Test 3: Headline Terminal Punctuation Rejection
// ──────────────────────────────────────────────────────────────────────────────
console.log('3. Testing Headline Terminal Punctuation Rejection in Zod...');
const badHeadlineFixture = {
  ...fixture3Scenes,
  scenes: [
    {
      ...fixture3Scenes.scenes[0],
      kinetic_text: 'ILLEGAL PERIOD.', // Period at end
    },
    fixture3Scenes.scenes[1],
    fixture3Scenes.scenes[2],
  ],
};

let rejected = false;
try {
  validateStoryboardSpec(badHeadlineFixture);
} catch (e: any) {
  rejected = true;
  console.log('   (Caught error: ' + e.message + ')');
  assert(e.message.toLowerCase().includes('terminal punctuation'), 'Error must explicitly mention terminal punctuation');
}
assert(rejected, 'Zod validator MUST reject headline with trailing period');
console.log('   ✅ Trailing period correctly rejected.');

// ──────────────────────────────────────────────────────────────────────────────
// Test 4: Scene Assembly with Direct Spec Layout and Transitions
// ──────────────────────────────────────────────────────────────────────────────
console.log('4. Testing Scene Assembler with Dynamic Layout and Transitions...');

const mockBrand: BrandJson = {
  name: 'PrismCloud',
  domain: 'prismcloud.io',
  tagline: 'Lightning fast developer platform.',
  description: 'Deploy distributed backends with zero configuration.',
  products: ['Edge Functions', 'Global DB', 'Realtime Sync'],
  logo: { src: '', text: 'PrismCloud', alt: 'PrismCloud', source: '' },
  colors: {
    accent: '#6366F1',
    accentLight: '#818CF8',
    background: '#09090B',
    background2: '#18181B',
    text: '#F9FAFB',
    muted: '#9CA3AF',
    surface: '#18181B',
    surfaceText: '#FFFFFF',
    surfaceMuted: '#6B7280',
  },
  fonts: { display: { family: 'Inter', source: 'Google Fonts' }, body: { family: 'Inter', source: 'Google Fonts' } },
  imagery: [],
  claims: [],
};

try {
  const assembled3 = assembleScenes({
    storyboard: fixture3Scenes,
    brand: mockBrand,
    jobId: 'test-job-3',
    fps: 60,
  });

  assert(assembled3.spec.scenes.length === 3, 'Assembled spec must contain exactly 3 scenes');
  assert(assembled3.spec.scenes[0].layout === 'hero-type', 'Scene 1 layout must be hero-type');
  assert(assembled3.spec.scenes[1].layout === 'split', 'Scene 2 layout must be split');
  assert(assembled3.spec.scenes[2].layout === 'cta', 'Scene 3 layout must be cta');
  assert(assembled3.spec.scenes[0].transitionOut === 'carousel_glide', 'Scene 1 transition must match spec');
  assert(assembled3.spec.scenes[1].transitionOut === 'wipe', 'Scene 2 transition must match spec');

  const assembled7 = assembleScenes({
    storyboard: fixture7Scenes,
    brand: mockBrand,
    jobId: 'test-job-7',
    fps: 60,
  });

  assert(assembled7.spec.scenes.length === 7, 'Assembled spec must contain exactly 7 scenes');
  assert(assembled7.spec.durationSec === 28.0, 'Assembled total duration must be 28.0s');
  console.log('   ✅ Scene Assembler successfully assembled 3-scene and 7-scene specs directly from storyboard.');
} finally {
  const jobsRoot = path.resolve(process.cwd(), 'jobs');
  fs.rmSync(path.join(jobsRoot, 'test-job-3'), { recursive: true, force: true });
  fs.rmSync(path.join(jobsRoot, 'test-job-7'), { recursive: true, force: true });
}

console.log('\n🎉 ALL PHASE 6 TESTS PASSED SUCCESSFULLY!');
