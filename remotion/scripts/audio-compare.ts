import {spawnSync, execFileSync} from 'node:child_process';
import {readFileSync, existsSync, mkdirSync, copyFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {mediaTools} from './media-tools.mjs';

const {ffmpeg} = mediaTools();
const root = process.cwd();

const jobId = process.argv[2] || 'promo-chatgpt-saas';
const jobDir = resolve(root, 'jobs', jobId);
const outDir = resolve(jobDir, 'out');
const specPath = resolve(jobDir, 'spec.json');

if (!existsSync(specPath)) {
  console.error(`Spec not found: ${specPath}`);
  process.exit(1);
}

mkdirSync(outDir, {recursive: true});
const spec = JSON.parse(readFileSync(specPath, 'utf8'));
const durationSec = spec.durationSec || 10;

console.log('='.repeat(78));
console.log(`AUDIO A/B/C COMPARISON PIPELINE: ${jobId.toUpperCase()}`);
console.log('='.repeat(78));

// 1. GENERATE OPTION A: Pure SFX Engine v2 (DSP / FFmpeg Millisecond Synthesis)
console.log('\n[1/4] Generating Option A: Pure SFX Engine v2 (FFmpeg DSP)...');
const optAOut = resolve(outDir, 'audio-option-a-sfx-v2.wav');
const sfxAssets = spec.audio.sfxFiles || {};
const items: {timeSec: number; type: string; gain: number; file: string}[] = [];

for (const scene of spec.scenes) {
  for (const cue of scene.sfx || []) {
    const absTime = Math.round((scene.start + cue.t) * 1000) / 1000;
    const relFile = sfxAssets[cue.type];
    if (relFile) {
      const fullPath = resolve(jobDir, 'assets', relFile);
      if (existsSync(fullPath)) {
        items.push({
          timeSec: absTime,
          type: cue.type,
          gain: cue.gain ?? 0.8,
          file: fullPath,
        });
      }
    }
  }
}
items.sort((a, b) => a.timeSec - b.timeSec);

const inputArgs: string[] = ['-f', 'lavfi', '-t', String(durationSec), '-i', 'anullsrc=r=48000:cl=stereo'];
const filterParts: string[] = [];

items.forEach((item, index) => {
  inputArgs.push('-i', item.file);
  const inIdx = index + 1;
  const delayMs = Math.round(item.timeSec * 1000);
  filterParts.push(`[${inIdx}:a]adelay=${delayMs}|${delayMs},volume=${item.gain.toFixed(2)}[a${inIdx}]`);
});

const mixInputs = ['[0:a]', ...items.map((_, i) => `[a${i + 1}]`)].join('');
const filterComplex = `${filterParts.join(';')};${mixInputs}amix=inputs=${items.length + 1}:dropout_transition=0:normalize=0[out]`;

execFileSync(ffmpeg, [
  '-hide_banner', '-y',
  ...inputArgs,
  '-filter_complex', filterComplex,
  '-map', '[out]',
  '-c:a', 'pcm_s24le',
  '-ar', '48000',
  '-t', String(durationSec),
  optAOut,
]);
console.log(`✓ Option A exported: ${optAOut}`);

// 2. EXTRACT OPTION B: Pure Remotion Native Audio (From raw.mp4)
console.log('\n[2/4] Extracting Option B: Pure Remotion Native Audio (Raw WebAudio)...');
const rawMp4 = resolve(outDir, 'raw.mp4');
const optBOut = resolve(outDir, 'audio-option-b-remotion-native.wav');

if (!existsSync(rawMp4)) {
  console.error(`raw.mp4 missing in ${outDir}. Run 'npm run render:job ${jobId}' first.`);
  process.exit(1);
}

execFileSync(ffmpeg, [
  '-hide_banner', '-y',
  '-i', rawMp4,
  '-vn',
  '-c:a', 'pcm_s24le',
  '-ar', '48000',
  '-t', String(durationSec),
  optBOut,
]);
console.log(`✓ Option B exported: ${optBOut}`);

// 3. GENERATE OPTION C: Combined Hybrid Master (Remotion Frame Sync + EBU R128 Broadcast DSP)
console.log('\n[3/4] Generating Option C: Combined Hybrid Master (Broadcast EBU R128 + Limiter)...');
const optCOut = resolve(outDir, 'audio-option-c-hybrid-master.wav');

execFileSync(ffmpeg, [
  '-hide_banner', '-y',
  '-i', optBOut,
  '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7',
  '-c:a', 'pcm_s24le',
  '-ar', '48000',
  '-t', String(durationSec),
  optCOut,
]);
console.log(`✓ Option C exported: ${optCOut}`);

// 4. MEASURE TELEMETRY ACROSS ALL 3 TRACKS
console.log('\n[4/4] Measuring Telemetry (LUFS, True Peak, LRA) across all 3 tracks:');
const measureLoudness = (filePath: string) => {
  const res = spawnSync(ffmpeg, [
    '-hide_banner',
    '-i', filePath,
    '-af', 'ebur128=framelog=verbose',
    '-f', 'null',
    '-',
  ], {encoding: 'utf8'});

  const out = res.stderr || '';
  const integratedMatch = out.match(/I:\s+([-\d.]+)\s+LUFS/);
  const peakMatch = out.match(/Peak:\s+([-\d.]+)\s+dBFS/);
  const lraMatch = out.match(/LRA:\s+([-\d.]+)\s+LU/);

  return {
    integrated: integratedMatch ? `${integratedMatch[1]} LUFS` : 'N/A',
    truePeak: peakMatch ? `${peakMatch[1]} dBFS` : 'N/A',
    lra: lraMatch ? `${lraMatch[1]} LU` : 'N/A',
  };
};

const telemetryA = measureLoudness(optAOut);
const telemetryB = measureLoudness(optBOut);
const telemetryC = measureLoudness(optCOut);

console.log('\n==============================================================================');
console.log('A/B/C AUDIO TELEMETRY COMPARISON SUMMARY:');
console.log('==============================================================================');
console.log(`Option A (Pure SFX Engine v2)   : Integrated: ${telemetryA.integrated} | Peak: ${telemetryA.truePeak} | LRA: ${telemetryA.lra}`);
console.log(`Option B (Pure Remotion Native) : Integrated: ${telemetryB.integrated} | Peak: ${telemetryB.truePeak} | LRA: ${telemetryB.lra}`);
console.log(`Option C (Combined Hybrid Master): Integrated: ${telemetryC.integrated} | Peak: ${telemetryC.truePeak} | LRA: ${telemetryC.lra}`);
console.log('==============================================================================\n');

// Copy tracks to artifact directory
const artifactDir = 'C:\\Users\\hemam\\.gemini\\antigravity\\brain\\3c4eb451-d156-463b-b133-6448310f27b8';
if (existsSync(artifactDir)) {
  copyFileSync(optAOut, resolve(artifactDir, 'chatgpt-audio-option-a-sfx-v2.wav'));
  copyFileSync(optBOut, resolve(artifactDir, 'chatgpt-audio-option-b-remotion-native.wav'));
  copyFileSync(optCOut, resolve(artifactDir, 'chatgpt-audio-option-c-hybrid-master.wav'));
  console.log(`Copied all 3 tracks to artifact directory: ${artifactDir}`);
}
