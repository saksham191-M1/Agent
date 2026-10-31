/**
 * produce-ad.ts
 * ─────────────
 * Master orchestrator. One command to produce a unique SaaS video for any product.
 *
 * Usage:
 *   npx tsx scripts/produce-ad.ts --url https://swiggy.com --name Swiggy --job swiggy-v1
 *   npx tsx scripts/produce-ad.ts --url https://linear.app --job linear-v2
 *   npx tsx scripts/produce-ad.ts --name "My SaaS" --desc "Description of product" --job my-saas-v1
 *
 * Pipeline:
 *   1. scrape-brand.ts   → brand.json  (Playwright, system Chrome)
 *   2. brain_opus.py     → storyboard.json  (Gemini AI + ML prompt matcher)
 *   3. scene-assembler.ts → ui_tree.json + spec.json
 *   4. ingest-template.ts → scenes/index.tsx (dynamic, non-hardcoded)
 *   5. render-raw.ts     → jobs/<jobId>/out/raw.mp4
 */

import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {scrapeBrand} from './scrape-brand';
import {assembleScenes} from './scene-assembler';
import {generateJobRegistry} from './job-discovery';
import {getCachedBrand, saveBrandToCache} from './brand-cache';
import {validateJob} from './lib/job-guard';
import type {BrandJson} from '../engine/types';

// ──────────────────────────────────────────────────────────────────────────────
// Args
// ──────────────────────────────────────────────────────────────────────────────

function parseArgs(): Record<string, string> {
  const argv = process.argv.slice(2);
  const parsed: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      const val = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : 'true';
      parsed[key] = val;
      if (val !== 'true') i++;
    }
  }
  return parsed;
}

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────

const VENV_PYTHON = path.resolve(
  process.cwd(),
  '..',   // go up from remotion/ to jarvis/
  'venv',
  'Scripts',
  'python.exe'
);

const BRAIN_OPUS_PY = path.resolve(
  process.cwd(),
  '..',
  'tools',
  'video_pipeline',
  'brain_opus.py'
);

function banner(msg: string) {
  const line = '─'.repeat(60);
  console.log(`\n${line}\n  ${msg}\n${line}`);
}

function step(n: number, label: string) {
  console.log(`\n[${n}/5] ${label}`);
}

function runRender(jobId: string): boolean {
  banner(`🎬 Rendering job: ${jobId}`);
  const result = spawnSync(
    'npx',
    ['tsx', 'scripts/render-raw.ts', '--job', jobId],
    {cwd: process.cwd(), stdio: 'inherit', shell: true}
  );
  return result.status === 0;
}

// ──────────────────────────────────────────────────────────────────────────────
// Step 3b: Write scenes/index.tsx (dynamic — reads ui_tree.json)
// ──────────────────────────────────────────────────────────────────────────────

function writeSceneEntry(jobId: string) {
  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const scenesDir = path.join(jobDir, 'scenes');
  fs.mkdirSync(scenesDir, {recursive: true});

  // This TSX is intentionally minimal and generic — it delegates all rendering
  // to VectorRenderer which reads ui_tree.json. No brand literals here.
  const tsx = `import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import type {SceneRendererProps} from '../../../engine';
import {VectorRenderer} from '../../../engine/semantic-ui/VectorRenderer';
import type {UITree, VectorNode} from '../../../engine/semantic-ui/types';
import {enterSpring, scaleIn} from '../../../engine/motion/presets';
import {Captions} from '../../../engine/components/Captions';
import uiTreeData from '../ui_tree.json';
import brandData from '../brand.json';

const SANS = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

const Scene: React.FC<SceneRendererProps> = ({scene, tokens}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const tree  = uiTreeData as unknown as UITree;
  const brand = brandData as any;
  const nodes = tree.nodes || [];

  // Motion preset: enterSpring
  const entrance = enterSpring(frame, fps);
  const progress = frame / durationInFrames;

  // Match active node to current scene (e.g. "scene_1" -> index 0)
  const matchIdx = scene?.id ? parseInt(scene.id.replace('scene_', ''), 10) - 1 : 0;
  const active  = (matchIdx >= 0 && matchIdx < nodes.length ? nodes[matchIdx] : nodes[0]) as VectorNode;

  // Merge brand colors into tokens so every node gets real brand identity
  const mergedTokens = {
    ...tokens,
    name: brand.name,
    colors: {...tokens.colors, ...brand.colors},
    fontFamily: brand.fonts?.display?.family || tokens.fontFamily,
    displayFontFamily: brand.fonts?.display?.family || tokens.fontFamily,
  };

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        backgroundColor: brand.colors?.background || tokens.colors.background,
        backgroundImage: \`radial-gradient(circle at 50% 30%, \${brand.colors?.accent || tokens.colors.accent}18 0%, transparent 70%),
                          radial-gradient(circle at 80% 80%, \${brand.colors?.background2 || tokens.colors.background2} 0%, \${brand.colors?.background || tokens.colors.background} 100%)\`,
        overflow: 'hidden',
        fontFamily: SANS,
      }}
    >
      {/* Subtle grid overlay adapted to theme */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: \`linear-gradient(to right, \${tokens.colors.hairline || 'rgba(255,255,255,0.05)'} 1px, transparent 1px), linear-gradient(to bottom, \${tokens.colors.hairline || 'rgba(255,255,255,0.05)'} 1px, transparent 1px)\`,
          backgroundSize: '48px 48px',
          pointerEvents: 'none',
        }}
      />

      {/* Brand accent glow */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          backgroundColor: brand.colors?.accent || tokens.colors.accent,
          filter: 'blur(180px)',
          opacity: 0.1,
          top: '10%',
          left: '30%',
          pointerEvents: 'none',
        }}
      />

      {/* 3D Spatial Stage with Continuous Camera Push and Dynamic Perspective */}
      <div
        style={{
          perspective: 1200,
          perspectiveOrigin: '50% 50%',
          transformStyle: 'preserve-3d',
          transform: \`scale(\${scaleIn(entrance) * (1 + progress * 0.05)}) translateY(\${(1 - entrance) * 35}px)\`,
          opacity: entrance,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
        }}
      >
        {active && (
          <VectorRenderer
            node={active}
            tokens={mergedTokens as any}
            sheenProgress={progress}
          />
        )}
      </div>

      {/* Subtitles & Captions */}
      {scene?.captionWords && scene.captionWords.length > 0 && (
        <Captions
          tokens={mergedTokens as any}
          words={scene.captionWords}
          sceneFrame={frame}
          visible={true}
        />
      )}
    </div>
  );
};

export default Scene;
`;

  fs.writeFileSync(path.join(scenesDir, 'index.tsx'), tsx, 'utf8');
  console.log(`[produce-ad] ✅ scenes/index.tsx written (dynamic, brand-driven)`);
}

// ──────────────────────────────────────────────────────────────────────────────
// Main
// ──────────────────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs();
  const url    = args['url']  || '';
  const name   = args['name'] || '';
  const desc   = args['desc'] || '';
  const jobId  = args['job']  || `job-${Date.now()}`;
  const skipScrape  = args['skip-scrape'] === 'true';
  const skipBrain   = args['skip-brain'] === 'true';
  const skipRender  = args['skip-render'] === 'true';

  if (!url && !name) {
    console.error('Error: provide --url <product_url> or --name <product_name>');
    process.exit(1);
  }

  banner(`🚀 PRODUCE-AD: ${name || url} → ${jobId}`);

  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  fs.mkdirSync(path.join(jobDir, 'assets', 'audio'), {recursive: true});
  fs.mkdirSync(path.join(jobDir, 'scenes'), {recursive: true});
  fs.mkdirSync(path.join(jobDir, 'out', 'stills'), {recursive: true});

  // Copy standard SFX assets from central modern sound pack
  const candidateAudioDirs = [
    path.resolve(process.cwd(), 'assets', 'default', 'audio'),
    path.resolve(process.cwd(), '..', 'assets', 'default', 'audio'),
    path.resolve(process.cwd(), 'public', 'audio'),
  ];
  const sfxSrc = candidateAudioDirs.find(d => fs.existsSync(d) && fs.existsSync(path.join(d, 'click.wav')));
  if (sfxSrc) {
    for (const f of ['room-tone.wav', 'click.wav', 'tick.wav', 'pop.wav', 'pop2.wav', 'swipe.wav', 'whoosh.wav', 'riser.wav', 'success.wav', 'logo-sting.wav', 'music-bed.mp3']) {
      const src = path.join(sfxSrc, f);
      const dst = path.join(jobDir, 'assets', 'audio', f);
      if (fs.existsSync(src) && !fs.existsSync(dst)) fs.copyFileSync(src, dst);
    }
  }

  // ─────────────────────────────────────────────────────────────────────
  // Step 1: Scrape brand
  // ─────────────────────────────────────────────────────────────────────
  let brand: BrandJson;
  const brandPath = path.join(jobDir, 'brand.json');

  if (skipScrape && fs.existsSync(brandPath)) {
    step(1, `Scrape skipped — loading existing brand.json`);
    brand = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
  } else {
    step(1, `Resolving brand tokens for ${url || name}`);
    if (url) {
      brand = await scrapeBrand(url, jobId);
    } else {
      const cached = getCachedBrand(name);
      if (cached) {
        console.log(`[produce-ad] ⚡ Found existing saved brand tokens for "${name}" in cache.`);
        brand = {...cached};
      } else {
        brand = {
          name,
          domain: `${name.toLowerCase().replace(/\s+/g, '')}.com`,
          tagline: desc.split('.')[0] || `${name} — built for what's next.`,
          description: desc || `${name} is a modern product.`,
          products: [name],
          logo: {src: `jobs/${jobId}/assets/logo.png`, text: name, alt: `${name} Logo`, source: ''},
          colors: {accent: '#6366F1', accentLight: '#818CF8', background: '#09090B', background2: '#18181B', text: '#F9FAFB', muted: '#9CA3AF', surface: '#18181B', surfaceText: '#FFFFFF', surfaceMuted: '#6B7280'},
          fonts: {display: {family: 'Inter, sans-serif', source: 'Google Fonts'}, body: {family: 'Inter, sans-serif', source: 'Google Fonts'}},
          imagery: [],
          claims: [{id: 'main', label: name, value: 'See it in action', sourceUrl: ''}],
        };
        saveBrandToCache(name, brand);
      }
      fs.writeFileSync(brandPath, JSON.stringify(brand, null, 2), 'utf8');
      console.log(`[produce-ad] ✅ brand.json dynamically configured for ${brand.name}`);
    }
  }
  console.log(`[produce-ad] Brand: ${brand.name} (${brand.domain}) accent=${brand.colors.accent}`);

  // ─────────────────────────────────────────────────────────────────────
  // Step 2: Run AI brain → storyboard.json
  // ─────────────────────────────────────────────────────────────────────
  const storyboardPath = path.join(jobDir, 'storyboard.json');
  const opusStoryboardPath = path.join(jobDir, 'storyboard.opus.json');

  if (skipBrain && (fs.existsSync(opusStoryboardPath) || fs.existsSync(storyboardPath))) {
    step(2, `Brain skipped — using existing storyboard blueprint`);
  } else {
    step(2, `Running Opus AI brain for: ${brand.name}`);

    if (!fs.existsSync(VENV_PYTHON)) {
      console.warn(`\n[produce-ad] ⚠️⚠️⚠️ LOUD WARNING: Python venv not found at ${VENV_PYTHON}`);
      console.warn(`[produce-ad] ⚠️⚠️⚠️ FALLBACK STORYBOARD USED FOR ${brand.name} — NO AI CREATIVE DIRECTION WAS RUN!`);
      const pageTitle = brand.tagline || brand.name;
      const fallback = {
        product_name: brand.name,
        matched_opus_category: 'MOTION',
        selected_template: 'Minimal Title Fallback',
        scenes: [
          {scene_id: 1, duration_seconds: 4, voiceover: `${brand.name}: ${pageTitle}`, veo_prompt: 'Product title overview', visual_fx: 'fast_zoom',  kinetic_text: brand.name.toUpperCase(),  requires_ui_image: false},
          {scene_id: 2, duration_seconds: 5, voiceover: `Explore ${brand.name}.`,       veo_prompt: 'App interface reveal',   visual_fx: 'glass_ui',   kinetic_text: brand.name.toUpperCase(),  requires_ui_image: true},
          {scene_id: 3, duration_seconds: 4, voiceover: `${brand.name} interface walkthrough.`, veo_prompt: 'Interface demo', visual_fx: 'push_right', kinetic_text: brand.name.toUpperCase(), requires_ui_image: true},
          {scene_id: 4, duration_seconds: 3, voiceover: `Visit ${brand.domain}.`,       veo_prompt: 'Logo outro',      visual_fx: 'fade_up',    kinetic_text: brand.name.toUpperCase(), requires_ui_image: false},
        ],
      };
      fs.writeFileSync(storyboardPath, JSON.stringify(fallback, null, 2), 'utf8');
    } else {
      const productDesc = desc || brand.description;
      const result = spawnSync(
        VENV_PYTHON,
        [BRAIN_OPUS_PY, brand.name, productDesc, '--output-json', storyboardPath],
        {cwd: path.dirname(BRAIN_OPUS_PY), stdio: 'inherit', encoding: 'utf8'}
      );
      if (result.status !== 0) {
        console.error(`[produce-ad] ❌ brain_opus.py failed with exit code ${result.status}`);
        process.exit(1);
      }
    }
  }

  if (!fs.existsSync(storyboardPath)) {
    console.error(`[produce-ad] ❌ storyboard.json was not created — check brain_opus.py output`);
    process.exit(1);
  }

  const actualStoryboardPath = (skipBrain && fs.existsSync(opusStoryboardPath)) ? opusStoryboardPath : storyboardPath;
  const storyboard = JSON.parse(fs.readFileSync(actualStoryboardPath, 'utf8'));
  console.log(`[produce-ad] ✅ Storyboard: ${storyboard.scenes?.length} scenes, template="${storyboard.selected_template}"`);

  // ─────────────────────────────────────────────────────────────────────
  // Step 3: Assemble scenes → ui_tree.json + spec.json
  // ─────────────────────────────────────────────────────────────────────
  step(3, `Assembling scenes for: ${brand.name} (${storyboard.scenes?.length} scenes)`);
  assembleScenes({storyboard, brand, jobId, fps: 60, format: args['format'] as any});

  // Validate job right after spec is written
  const guardAfterSpec = validateJob(path.resolve(process.cwd(), 'jobs'), jobId);
  if (!guardAfterSpec.valid) {
    if (args['force'] === 'true') {
      console.warn(`\n⚠️  [JOB GUARD WARNING] Proceeding after spec creation due to --force flag:`);
      for (const err of guardAfterSpec.errors) {
        console.warn(`  - [${err.code}] ${err.message}`);
      }
    } else {
      console.error(`\n❌ [JOB GUARD FAILED] Spec validation failed for ${jobId}:`);
      for (const err of guardAfterSpec.errors) {
        console.error(`  - [${err.code}] ${err.message}`);
      }
      process.exit(1);
    }
  }

  // ─────────────────────────────────────────────────────────────────────
  // Step 4: Write scenes/index.tsx (generic, brand-driven)
  // ─────────────────────────────────────────────────────────────────────
  step(4, `Writing scenes/index.tsx`);
  writeSceneEntry(jobId);
  try {
    generateJobRegistry(process.cwd());
    console.log(`[produce-ad] ✅ Job registry updated for Remotion root`);
  } catch (regErr) {
    console.warn(`[produce-ad] Warning updating job registry:`, regErr);
  }

  // ─────────────────────────────────────────────────────────────────────
  // Step 5: Render
  // ─────────────────────────────────────────────────────────────────────
  if (skipRender) {
    step(5, `Render skipped (--skip-render)`);
    console.log(`\n✅ Pipeline complete (no render). Artifacts in: jobs/${jobId}/`);
  } else {
    step(5, `Rendering video: ${jobId}`);
    const ok = runRender(jobId);
    if (ok) {
      const outPath = path.join(jobDir, 'out', 'raw.mp4');
      banner(`✅ SUCCESS — ${brand.name} ad produced!\n  → ${outPath}`);
    } else {
      console.error(`[produce-ad] ❌ Render failed. Check Remotion output above.`);
      process.exit(1);
    }
  }
}

main().catch(err => {
  console.error(`[produce-ad] Fatal error:`, err);
  process.exit(1);
});
