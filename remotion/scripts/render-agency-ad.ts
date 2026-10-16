import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {EcprojBuilder} from '../engine/effectcraft/ecproj-builder';
import {EffectCraftBridge} from './effectcraft-bridge';
import {stageJobAssets} from './stage-assets';
import type {BrandJson} from '../engine/types';
import type {UITree} from '../engine/semantic-ui/types';
import type {CameraFlightPath} from '../engine/stage/types';

async function main() {
  const args = process.argv.slice(2);
  const jobId = args.find((a) => !a.startsWith('--')) || 'sample-promo-prisma';
  const forceEffectCraft = args.includes('--engine=effectcraft');

  console.log(`\n======================================================`);
  console.log(`🚀 AI AD DIRECTOR: RENDERING AGENCY-TIER MOTION AD [${jobId}]`);
  console.log(`Engine Mode:        ${forceEffectCraft ? 'EffectCraft (Native Skia/AE)' : 'Remotion Web Compositor (Interactive Web Graphics)'}`);
  console.log(`======================================================\n`);

  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const outDir = path.join(jobDir, 'out');
  fs.mkdirSync(outDir, {recursive: true});
  const mp4OutPath = path.join(outDir, 'agency_tier_ad.mp4');

  if (forceEffectCraft) {
    const brand: BrandJson = JSON.parse(fs.readFileSync(path.join(jobDir, 'brand.json'), 'utf8'));
    const uiTree: UITree = JSON.parse(fs.readFileSync(path.join(jobDir, 'ui_tree.json'), 'utf8'));
    const cameraFlight: CameraFlightPath = JSON.parse(fs.readFileSync(path.join(jobDir, 'camera_flight.json'), 'utf8'));

    const jsxPath = path.join(jobDir, 'agency_motion.jsx');
    const ecprojPath = path.join(jobDir, 'agency_motion.ecproj');

    console.log(`[Layer 1 & 2] Compiling Semantic UI AST & Continuous 3D Camera Flight...`);
    EcprojBuilder.writeJsxScript(
      {
        compName: 'AgencyStage',
        width: uiTree.worldBounds?.width || 1920,
        height: uiTree.worldBounds?.height || 1080,
        fps: 30,
        durationSec: 8.0,
        brand,
        uiTree,
        cameraFlight,
        outputEcprojPath: ecprojPath,
      },
      jsxPath
    );

    console.log(`\n[Layer 5] Building native EffectCraft composition...`);
    EffectCraftBridge.buildProjectFromJsx(jsxPath, ecprojPath);

    console.log(`\n[Render Engine] Triggering headless EffectCraft After Effects compositor...`);
    const renderRes = EffectCraftBridge.render({
      projectPath: ecprojPath,
      compName: 'AgencyStage',
      outputPath: mp4OutPath,
      startSec: 0,
      endSec: 8.0,
      fps: 30,
    });

    if (renderRes.success) {
      console.log(`\n🎉 EFFECTCRAFT AD RENDERED SUCCESSFULLY! Output: ${renderRes.outputPath}\n`);
      return;
    }
    console.log(`EffectCraft render failed or unavailable. Falling back to Remotion Web Compositor...`);
  }

  // Remotion Web Compositor Render Path
  console.log(`[Render Engine] Triggering Remotion Web Compositor (macOS Chrome, Glassmorphic Bento Cards, SVG Sparklines)...`);
  const root = process.cwd();
  stageJobAssets(root, jobId);

  const rawScript = path.resolve(root, 'scripts', 'render-raw.ts');
  const tsxCli = path.resolve(root, 'node_modules', 'tsx', 'dist', 'cli.mjs');
  const startTime = Date.now();
  execFileSync(process.execPath, [tsxCli, rawScript, jobId], {
    stdio: 'inherit',
    env: {...process.env, AD_JOB_ID: jobId},
  });

  const rawMp4 = path.join(outDir, 'raw.mp4');
  if (fs.existsSync(rawMp4)) {
    fs.copyFileSync(rawMp4, mp4OutPath);
  }
  const durationSec = ((Date.now() - startTime) / 1000).toFixed(2);

  console.log(`\n🎉 REMOTION WEB COMPOSITOR RENDER COMPLETE!`);
  console.log(`------------------------------------------------------`);
  console.log(`Engine:             Remotion Web Compositor (Rich SaaS UI Widgets)`);
  console.log(`Output Video:       ${mp4OutPath}`);
  console.log(`Render Time:        ${durationSec}s`);
  console.log(`Widgets Rendered:   macOS IDE Terminal, Live SVG Sparkline, Glassmorphic Bento Grid, Pulsing Status Dots`);
  console.log(`------------------------------------------------------\n`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
