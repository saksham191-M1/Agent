import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {installedBrowser, mediaTools} from './media-tools.mjs';

const require = createRequire(import.meta.url);
let stage = 'dependencies';
try {
  const {openBrowser} = await import('@remotion/renderer');
  require.resolve('@remotion/bundler');
  stage = 'native';
  // tsx can have its own esbuild version. Probe the loader used by exports,
  // rather than a different, hoisted esbuild installation.
  createRequire(require.resolve('tsx'))('esbuild').transformSync('const value: number = 1', {loader: 'ts'});
  stage = 'encoders';
  const tools = mediaTools();
  for (const tool of Object.values(tools)) execFileSync(tool, ['-version'], {stdio: 'ignore', timeout: 10000});
  stage = 'browser';
  const browserExecutable = installedBrowser(process.cwd());
  const browser = await openBrowser('chrome', {browserExecutable, logLevel: 'error'});
  await browser.close({silent: true});
  process.stdout.write(JSON.stringify({ready: true, platform: process.platform, browser: browserExecutable, ...tools}));
} catch (error) {
  const hints = {
    dependencies: 'Run npm ci in remotion-swiggy.',
    native: `Run npm ci on ${process.platform}; Windows and Linux/WSL need separate node_modules installations.`,
    encoders: 'Install FFmpeg/ffprobe or configure FFMPEG_PATH and FFPROBE_PATH for this OS.',
    browser: 'Run npx remotion browser ensure, or set REMOTION_BROWSER_EXECUTABLE. On Linux, install Chromium\'s shared libraries.',
  };
  const detail = String(error instanceof Error ? error.message : error).slice(0, 1600);
  process.stdout.write(JSON.stringify({ready: false, platform: process.platform, stage, reason: hints[stage], detail}));
  process.exitCode = 1;
}
