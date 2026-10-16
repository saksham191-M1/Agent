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
import {useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
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
      {/* Subtle grid overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px)',
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

      {/* Main semantic stage */}
      <div
        style={{
          transform: \`scale(\${scaleIn(entrance)}) translateY(\${(1 - entrance) * 35}px)\`,
          opacity: entrance,
          zIndex: 10,
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

  // Copy standard SFX assets
  const sfxSrc = path.resolve(process.cwd(), 'jobs', 'swiggy-001', 'assets', 'audio');
  if (fs.existsSync(sfxSrc)) {
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
    step(1, `Scraping brand from ${url || 'no URL — building from name only'}`);
    if (url) {
      brand = await scrapeBrand(url, jobId);
    } else {
      // No URL: build minimal brand from --name and --desc
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
      fs.writeFileSync(brandPath, JSON.stringify(brand, null, 2), 'utf8');
      console.log(`[produce-ad] ✅ brand.json built from --name + --desc`);
    }
  }
  console.log(`[produce-ad] Brand: ${brand.name} (${brand.domain}) accent=${brand.colors.accent}`);

  // ─────────────────────────────────────────────────────────────────────
  // Step 2: Run AI brain → storyboard.json
  // ─────────────────────────────────────────────────────────────────────
  const storyboardPath = path.join(jobDir, 'storyboard.json');

  if (skipBrain && fs.existsSync(storyboardPath)) {
    step(2, `Brain skipped — using existing storyboard.json`);
  } else {
    step(2, `Running Opus AI brain for: ${brand.name}`);

    if (!fs.existsSync(VENV_PYTHON)) {
      console.warn(`[produce-ad] ⚠️  Python venv not found at ${VENV_PYTHON}`);
      console.warn(`[produce-ad] ⚠️  Writing fallback storyboard.json`);
      const fallback = {
        product_name: brand.name,
        matched_opus_category: 'MOTION',
        selected_template: 'Problem-Agitate-Solution (UI Showcase)',
        scenes: [
          {scene_id: 1, duration_seconds: 4, voiceover: `The problem ${brand.name} solves.`, veo_prompt: 'Cinematic opener', visual_fx: 'fast_zoom',  kinetic_text: 'BROKEN',  requires_ui_image: false},
          {scene_id: 2, duration_seconds: 5, voiceover: `Introducing ${brand.name}.`,       veo_prompt: 'App UI reveal',   visual_fx: 'glass_ui',   kinetic_text: 'SOLVED',  requires_ui_image: true},
          {scene_id: 3, duration_seconds: 4, voiceover: `See ${brand.name} in action.`,     veo_prompt: 'Workflow demo',   visual_fx: 'push_right',  kinetic_text: 'FASTER',  requires_ui_image: true},
          {scene_id: 4, duration_seconds: 3, voiceover: `Start with ${brand.name} today.`,  veo_prompt: 'Logo outro',      visual_fx: 'fade_up',    kinetic_text: 'START NOW', requires_ui_image: false},
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

  const storyboard = JSON.parse(fs.readFileSync(storyboardPath, 'utf8'));
  console.log(`[produce-ad] ✅ Storyboard: ${storyboard.scenes?.length} scenes, template="${storyboard.selected_template}"`);

  // ─────────────────────────────────────────────────────────────────────
  // Step 3: Assemble scenes → ui_tree.json + spec.json
  // ─────────────────────────────────────────────────────────────────────
  step(3, `Assembling scenes for: ${brand.name} (${storyboard.scenes?.length} scenes)`);
  assembleScenes({storyboard, brand, jobId});

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
