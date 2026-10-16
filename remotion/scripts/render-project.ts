import {bundle} from '@remotion/bundler';
import {makeCancelSignal, openBrowser, renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import {createHash} from 'node:crypto';
import {cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {dirname, extname, resolve} from 'node:path';
import type {ProjectManifest} from '../engine/project-types';
import {installedBrowser} from './media-tools.mjs';
import {verifyProjectExport} from './project-qa.mjs';

const main = async () => {
const root = process.cwd();
const [manifestPath, outputPath] = process.argv.slice(2);
if (!manifestPath || !outputPath) throw new Error('Usage: render-project.ts <manifest.json> <output.mp4>');
const manifest = JSON.parse(readFileSync(resolve(manifestPath), 'utf8')) as ProjectManifest;
if (!['draft', 'final'].includes(manifest.quality) || !['9:16', '16:9', '1:1'].includes(manifest.format)
  || ![24, 30].includes(manifest.fps) || ![15, 20, 30].includes(manifest.durationSec)
  || !/^#[0-9a-f]{6}$/i.test(manifest.brief.color) || manifest.scenes.length !== 4) throw new Error('Invalid Jarvis project manifest.');
let end = 0;
for (const scene of manifest.scenes) {
  if (Math.abs(scene.start - end) > .005 || scene.duration < 2 || scene.duration > 12
    || Math.abs(scene.end - scene.start - scene.duration) > .005 || typeof scene.headline !== 'string') throw new Error('Non-contiguous or invalid project scene.');
  end = scene.end;
}
if (Math.abs(end - manifest.durationSec) > .005) throw new Error('Project scene timing does not match the export duration.');

const output = resolve(outputPath);
const directory = dirname(output);
mkdirSync(directory, {recursive: true});
const stageRoot = resolve(directory, 'assets');
const bundleRoot = resolve(directory, '.bundle');
const cancelFile = resolve(directory, 'cancel.requested');
mkdirSync(stageRoot, {recursive: true});
cpSync(resolve(root, 'public', 'fonts'), resolve(stageRoot, 'fonts'), {recursive: true});
const staged: Record<string, string> = {};
const assetHashes: Record<string, string> = {};
for (const [key, source] of Object.entries({...manifest.assets, ...(manifest.audio ? {audio: manifest.audio} : {})})) {
  if (!/^(logo|screenshot|demo|scene_[1-4]|audio)$/.test(key) || !existsSync(source)) throw new Error(`Missing or invalid asset: ${key}`);
  const name = `${key}${extname(source).toLowerCase()}`;
  cpSync(source, resolve(stageRoot, name));
  staged[key] = name;
  assetHashes[key] = createHash('sha256').update(readFileSync(source)).digest('hex');
}
const props = {manifest: {...manifest, assets: staged, audio: staged.audio ?? null}};
writeFileSync(resolve(directory, 'composition-props.json'), JSON.stringify(props, null, 2));
const cancellation = makeCancelSignal();
const timer = setInterval(() => {if (existsSync(cancelFile)) cancellation.cancel();}, 150);
let browser;
try {
  const serveUrl = await bundle({entryPoint: resolve(root, 'project-entry.tsx'), outDir: bundleRoot, publicDir: stageRoot, onProgress: (value) => console.log(`BUNDLE ${value}`)});
  if (existsSync(cancelFile)) throw new Error('Render cancelled.');
  const browserExecutable = installedBrowser(root);
  browser = await openBrowser('chrome', {browserExecutable, logLevel: 'error'});
  const composition = await selectComposition({serveUrl, id: 'ProjectAd', inputProps: props, puppeteerInstance: browser, logLevel: 'error'});
  await renderStill({serveUrl, composition, inputProps: props, puppeteerInstance: browser, output: resolve(directory, 'poster.jpg'), imageFormat: 'jpeg', frame: manifest.fps, overwrite: true, cancelSignal: cancellation.cancelSignal, logLevel: 'error'});
  // JPEG frames carry full-range color. Convert explicitly to limited-range
  // BT.709 so H.264 exports are consistently reported as yuv420p by ffprobe.
  await renderMedia({serveUrl, composition, inputProps: props, puppeteerInstance: browser, outputLocation: output, codec: 'h264', pixelFormat: 'yuv420p', colorSpace: 'bt709', audioCodec: 'aac', audioBitrate: '192k', sampleRate: 48000, crf: manifest.quality === 'draft' ? 24 : 18, overwrite: true, cancelSignal: cancellation.cancelSignal, concurrency: Number(process.env.STUDIO_REMOTION_CONCURRENCY ?? 2), logLevel: 'error', onProgress: ({progress, renderedFrames}) => console.log(`FRAME ${renderedFrames} ${progress.toFixed(3)}`)});
  const qa = verifyProjectExport(output, {width: composition.width, height: composition.height, fps: composition.fps, durationSec: manifest.durationSec, audio: Boolean(manifest.audio)});
  writeFileSync(resolve(directory, 'qa-report.json'), JSON.stringify({...qa, assetHashes, manifestSha256: createHash('sha256').update(readFileSync(manifestPath)).digest('hex')}, null, 2));
  console.log(`VERIFIED ${output}`);
} finally {
  clearInterval(timer);
  if (browser) await browser.close({silent: true});
  rmSync(bundleRoot, {recursive: true, force: true});
}
};
main().catch((error) => {console.error(error); process.exitCode = 1;});
