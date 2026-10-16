import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

export interface RenderResult {
  engine: 'effectcraft' | 'remotion-fallback';
  outputPath: string;
  renderDurationMs: number;
  success: boolean;
  error?: string;
}

export class EffectCraftBridge {
  private static getCliPath(): string {
    const localPath = path.resolve(
      process.cwd(),
      'bin',
      'effectcraft',
      'effectcraft-0.8.0-windows-x64-portable',
      'effectcraft-cli.exe'
    );
    if (fs.existsSync(localPath)) return localPath;
    return 'effectcraft-cli';
  }

  static isAvailable(): boolean {
    const cli = this.getCliPath();
    try {
      const res = spawnSync(cli, ['--version'], {encoding: 'utf8', timeout: 3000});
      return res.status === 0 && res.stdout.includes('effectcraft-cli');
    } catch {
      return false;
    }
  }

  static buildProjectFromJsx(jsxPath: string, ecprojOutPath: string): boolean {
    const cli = this.getCliPath();
    try {
      const res = spawnSync(cli, ['script', jsxPath, '--save-as', ecprojOutPath], {
        encoding: 'utf8',
        timeout: 10000,
      });
      return res.status === 0;
    } catch (e) {
      console.error('Failed to build .ecproj from JSX:', e);
      return false;
    }
  }

  static render(options: {
    projectPath: string;
    compName: string;
    outputPath: string;
    startSec?: number;
    endSec?: number;
    fps?: number;
  }): RenderResult {
    const startTime = Date.now();
    const cli = this.getCliPath();

    if (!this.isAvailable()) {
      return {
        engine: 'remotion-fallback',
        outputPath: options.outputPath,
        renderDurationMs: 0,
        success: false,
        error: 'EffectCraft CLI is not available on this system.',
      };
    }

    const args = [
      'render',
      '--project',
      options.projectPath,
      '--comp',
      options.compName,
      '--out',
      options.outputPath,
    ];

    if (options.startSec !== undefined) args.push('--start', String(options.startSec));
    if (options.endSec !== undefined) args.push('--end', String(options.endSec));
    if (options.fps !== undefined) args.push('--fps', String(options.fps));

    try {
      const res = spawnSync(cli, args, {encoding: 'utf8', timeout: 60000});
      const durationMs = Date.now() - startTime;

      if (res.status === 0 && fs.existsSync(options.outputPath)) {
        return {
          engine: 'effectcraft',
          outputPath: options.outputPath,
          renderDurationMs: durationMs,
          success: true,
        };
      } else {
        return {
          engine: 'remotion-fallback',
          outputPath: options.outputPath,
          renderDurationMs: durationMs,
          success: false,
          error: res.stderr || 'Render process exited with non-zero status.',
        };
      }
    } catch (err: any) {
      return {
        engine: 'remotion-fallback',
        outputPath: options.outputPath,
        renderDurationMs: Date.now() - startTime,
        success: false,
        error: err?.message || String(err),
      };
    }
  }
}

// CLI entrypoint support
if (process.argv[1]?.includes('effectcraft-bridge')) {
  const args = process.argv.slice(2);
  let jobId = 'agency-motion-001';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--job-id' && args[i + 1]) {
      jobId = args[i + 1];
      break;
    }
  }

  const {EcprojBuilder} = require('../engine/effectcraft/ecproj-builder');
  const jobDir = path.resolve(process.cwd(), 'jobs', jobId);
  const brand = JSON.parse(fs.readFileSync(path.join(jobDir, 'brand.json'), 'utf8'));
  const uiTree = JSON.parse(fs.readFileSync(path.join(jobDir, 'ui_tree.json'), 'utf8'));
  const cameraFlight = JSON.parse(fs.readFileSync(path.join(jobDir, 'camera_flight.json'), 'utf8'));

  const outDir = path.join(jobDir, 'out');
  fs.mkdirSync(outDir, {recursive: true});

  const jsxPath = path.join(jobDir, 'agency_motion.jsx');
  const ecprojPath = path.join(jobDir, 'agency_motion.ecproj');
  const mp4OutPath = path.join(outDir, 'agency_tier_ad.mp4');

  console.log(`[Bridge] Compiling ExtendScript for ${jobId}...`);
  EcprojBuilder.writeJsxScript(
    {
      compName: 'AgencyStage',
      width: uiTree.worldBounds.width || 1920,
      height: uiTree.worldBounds.height || 1080,
      fps: 30,
      durationSec: 8.0,
      brand,
      uiTree,
      cameraFlight,
      outputEcprojPath: ecprojPath,
    },
    jsxPath
  );

  console.log(`[Bridge] Building native EffectCraft project...`);
  EffectCraftBridge.buildProjectFromJsx(jsxPath, ecprojPath);

  console.log(`[Bridge] Rendering via EffectCraft CLI...`);
  const res = EffectCraftBridge.render({
    projectPath: ecprojPath,
    compName: 'AgencyStage',
    outputPath: mp4OutPath,
    startSec: 0,
    endSec: 8.0,
    fps: 30,
  });

  if (res.success) {
    console.log(`\n🎉 EFFECTCRAFT RENDER COMPLETE! Output: ${res.outputPath} (${(res.renderDurationMs / 1000).toFixed(2)}s)\n`);
  } else {
    console.error('Render failed:', res.error);
    process.exit(1);
  }
}
