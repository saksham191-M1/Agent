import {spawnSync} from 'node:child_process';
import {readFileSync, existsSync, mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {mediaTools} from './media-tools.mjs';

const {ffmpeg} = mediaTools();
const root = process.cwd();

const jobId = process.argv[2] || 'promo-chatgpt-saas';
const jobDir = resolve(root, 'jobs', jobId);
const specPath = resolve(jobDir, 'spec.json');

if (!existsSync(specPath)) {
  console.error(`Spec not found: ${specPath}`);
  process.exit(1);
}

const spec = JSON.parse(readFileSync(specPath, 'utf8'));
const durationSec = spec.durationSec || 10;
const sfxAssets = spec.audio.sfxFiles || {
  pop: 'audio/pop.wav',
  tick: 'audio/tick.wav',
  click: 'audio/click.wav',
};

// Collect all SFX events across scenes
interface SfxItem {
  timeSec: number;
  type: string;
  gain: number;
  file: string;
}

const items: SfxItem[] = [];

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
console.log(`Found ${items.length} SFX events for ${jobId}:`);
items.forEach((it, i) => {
  console.log(`  [${i + 1}] ${it.timeSec.toFixed(3)}s : [${it.type.toUpperCase()}] gain: ${it.gain}`);
});

const outDir = resolve(jobDir, 'out');
mkdirSync(outDir, {recursive: true});
const isolatedOut = resolve(outDir, 'chatgpt-sfx-v2-isolated.wav');

// Build FFmpeg complex filter to place each audio file at its exact millisecond offset
const inputArgs: string[] = [];
const filterParts: string[] = [];

// Base silence generator for exact duration
inputArgs.push('-f', 'lavfi', '-t', String(durationSec), '-i', 'anullsrc=r=48000:cl=stereo');

items.forEach((item, index) => {
  inputArgs.push('-i', item.file);
  const inIdx = index + 1;
  const delayMs = Math.round(item.timeSec * 1000);
  // Apply adelay and volume gain
  filterParts.push(`[${inIdx}:a]adelay=${delayMs}|${delayMs},volume=${item.gain.toFixed(2)}[a${inIdx}]`);
});

const mixInputs = ['[0:a]', ...items.map((_, i) => `[a${i + 1}]`)].join('');
const filterComplex = `${filterParts.join(';')};${mixInputs}amix=inputs=${items.length + 1}:dropout_transition=0:normalize=0[out]`;

const ffArgs = [
  '-hide_banner',
  '-y',
  ...inputArgs,
  '-filter_complex', filterComplex,
  '-map', '[out]',
  '-c:a', 'pcm_s24le',
  '-ar', '48000',
  '-t', String(durationSec),
  isolatedOut,
];

console.log('Synthesizing pure isolated SFX track via FFmpeg...');
const res = spawnSync(ffmpeg, ffArgs, {stdio: 'inherit'});

if (res.status === 0) {
  console.log(`Successfully generated isolated SFX track: ${isolatedOut}`);
} else {
  console.error('Failed to generate isolated SFX track.');
  process.exit(1);
}
