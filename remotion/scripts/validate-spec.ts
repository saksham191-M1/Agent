import {readFileSync, readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import Ajv from 'ajv/dist/2020.js';
import schema from '../engine/spec.schema.json';
import type {AdSpec} from '../engine';

const root = process.cwd();
const ajv = new Ajv({allErrors: true, strict: false});
const validate = ajv.compile(schema);
const jobs = readdirSync(resolve(root, 'jobs'), {withFileTypes: true}).filter((entry) => entry.isDirectory());
let failed = false;

for (const job of jobs) {
  const path = resolve(root, 'jobs', job.name, 'spec.json');
  const spec = JSON.parse(readFileSync(path, 'utf8')) as AdSpec;
  if (!validate(spec)) {
    failed = true;
    console.error(`${job.name}: schema invalid`, validate.errors);
    continue;
  }
  const sorted = [...spec.scenes].sort((a, b) => a.start - b.start);
  const end = sorted.at(-1)!.start + sorted.at(-1)!.duration;
  if (Math.abs(end - spec.durationSec) > 0.001) {
    failed = true;
    console.error(`${job.name}: scenes end at ${end}, expected ${spec.durationSec}`);
  }
   sorted.forEach((scene, index) => {
     if (scene.start < 0 || scene.start + scene.duration > spec.durationSec + 0.001) failed = true;
     if (index > 0 && scene.start < sorted[index - 1].start + sorted[index - 1].duration - 0.001) failed = true;
     const expectedStart = index === 0 ? 0 : sorted[index - 1].start + sorted[index - 1].duration;
     if (Math.abs(scene.start - expectedStart) > 0.001) {
       failed = true;
       console.error(`${job.name}: scene ${scene.id} is not contiguous at ${scene.start}; expected ${expectedStart}`);
     }
    if (scene.headline.trim().split(/\s+/).length > 8) failed = true;
    if (scene.subline.trim().split(/\s+/).length > 12) failed = true;
    if (index > 1 && scene.layout === sorted[index - 1].layout && scene.layout === sorted[index - 2].layout) failed = true;
  });
  console.log(`${job.name}: spec valid (${spec.scenes.length} scenes, ${spec.durationSec}s)`);
}

if (failed) process.exitCode = 1;
