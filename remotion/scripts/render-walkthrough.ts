import fs from 'node:fs';
import path from 'node:path';
import {WalkthroughEcprojBuilder} from '../engine/walkthrough/walkthrough-ecproj-builder';
import {EffectCraftBridge} from './effectcraft-bridge';
import type {SoftwareWalkthroughSpec} from '../engine/walkthrough/types';

async function main() {
  const jobId = process.argv[2] || 'walkthrough-demo-001';
  console.log(`\n======================================================`);
  console.log(`🚀 AI AD DIRECTOR: RENDERING SOFTWARE WALKTHROUGH [${jobId}]`);
  console.log(`======================================================\n`);

  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const specPath = path.join(jobDir, 'spec.v2.json');

  if (!fs.existsSync(specPath)) {
    console.error(`Missing spec.v2.json at ${specPath}`);
    process.exit(1);
  }

  const spec: SoftwareWalkthroughSpec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  const outDir = path.join(jobDir, 'out');
  fs.mkdirSync(outDir, {recursive: true});

  const jsxPath = path.join(jobDir, 'walkthrough.jsx');
  const ecprojPath = path.join(jobDir, 'walkthrough.ecproj');
  const mp4OutPath = path.join(outDir, 'walkthrough_ad.mp4');

  console.log(`[Layer 1 & 2] Compiling Dynamic 2D Auto-Zoom & Motor Physics Rig...`);
  WalkthroughEcprojBuilder.writeJsx(spec, jsxPath);
  console.log(`✓ Generated ExtendScript blueprint: ${jsxPath}`);

  console.log(`\n[Layer 5] Building native EffectCraft 2D composition...`);
  const buildSuccess = EffectCraftBridge.buildProjectFromJsx(jsxPath, ecprojPath);
  if (!buildSuccess) {
    console.error('Failed to compile .ecproj via EffectCraft CLI.');
    process.exit(1);
  }
  console.log(`✓ Compiled native project file: ${ecprojPath}`);

  console.log(`\n[Render Engine] Triggering headless EffectCraft After Effects compositor...`);
  const renderRes = EffectCraftBridge.render({
    projectPath: ecprojPath,
    compName: spec.metadata.title,
    outputPath: mp4OutPath,
    startSec: 0,
    endSec: 10.0,
    fps: spec.metadata.fps || 60,
  });

  if (renderRes.success) {
    console.log(`\n🎉 HIGH-DPI SOFTWARE WALKTHROUGH RENDERED SUCCESSFULLY!`);
    console.log(`------------------------------------------------------`);
    console.log(`Engine:             EffectCraft 0.8.0 Native After Effects Engine`);
    console.log(`Output Video:       ${renderRes.outputPath}`);
    console.log(`Resolution:         ${spec.metadata.width}x${spec.metadata.height} (High-DPI 2D Viewport)`);
    console.log(`Render Time:        ${(renderRes.renderDurationMs / 1000).toFixed(2)}s`);
    console.log(`Auto-Zoom:          Clamped 2D Focal Zoom (Screen Studio / Arcade Style)`);
    console.log(`Motor Rig:          Minimum-Jerk Human Physics + Click Impulse (0.86x)`);
    console.log(`------------------------------------------------------\n`);
  } else {
    console.error('Render failed:', renderRes.error);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
