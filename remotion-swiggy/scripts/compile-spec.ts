import {readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {listJobs} from '../jobs/registry';
import Ajv2020 from 'ajv/dist/2020.js';

const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}

const root = process.cwd();
const storyboardPath = resolve(root, 'jobs', jobId, 'storyboard.json');
const brandPath = resolve(root, 'jobs', jobId, 'brand.json');
const outDir = resolve(root, 'jobs', jobId, 'out');
import {mkdirSync} from 'node:fs';
try { mkdirSync(outDir, {recursive: true}); } catch { /* ignore */ }
const outPath = resolve(outDir, 'spec.compiled.json');

try {
  const storyboard = JSON.parse(readFileSync(storyboardPath, 'utf8'));
  const brand = JSON.parse(readFileSync(brandPath, 'utf8'));

  const spec = {
    brand: storyboard.passthrough?.brand || brand.brand,
    format: storyboard.passthrough?.format,
    fps: storyboard.passthrough?.fps,
    durationSec: storyboard.passthrough?.durationSec,
    bpm: storyboard.passthrough?.bpm,
    scenes: storyboard.shots.map((shot: any) => {
      return {
        id: shot.passthrough?.id || `scene_${shot.n}`,
        start: shot.t0,
        duration: shot.t1 - shot.t0,
        layout: shot.visual,
        headline: shot.headline || "",
        subline: shot.subline || "",
        caption: shot.onScreenText || "",
        captionWords: shot.passthrough?.captionWords || [],
        visual: shot.passthrough?.visualObj || {},
        motion: shot.passthrough?.motion || { enter: "fade", idle: "none", exit: "fade" },
        vo: shot.dialogue || "",
        sfx: shot.sfx || [],
        transitionOut: shot.transitionOut || "cut"
      };
    }),
    audio: storyboard.passthrough?.audio
  };

  const ajv = new Ajv2020();
  const schema = JSON.parse(readFileSync(resolve(root, 'engine/spec.schema.json'), 'utf8'));
  const validate = ajv.compile(schema);

  if (!validate(spec)) {
    console.error("Compiled spec is invalid:", validate.errors);
    process.exit(1);
  }

  writeFileSync(outPath, JSON.stringify(spec, null, 2));
  console.log(`Compiled spec successfully written to spec.compiled.json`);
} catch (e: any) {
  console.error("Compile spec failed:", e.message);
  process.exit(1);
}
