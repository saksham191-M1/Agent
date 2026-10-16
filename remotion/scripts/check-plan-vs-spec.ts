import {readFileSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {listJobs} from '../jobs/registry';

const root = process.cwd();
const jobs = listJobs();
let hasError = false;

jobs.forEach(job => {
  const sbPath = resolve(root, 'jobs', job, 'storyboard.json');
  const specPath = resolve(root, 'jobs', job, 'spec.json');
  const excPath = resolve(root, 'jobs', job, 'known-exceptions.json');
  
  const sb = JSON.parse(readFileSync(sbPath, 'utf8'));
  const spec = JSON.parse(readFileSync(specPath, 'utf8'));
  
  let exceptions: Record<string, string> = {};
  if (existsSync(excPath)) {
    exceptions = JSON.parse(readFileSync(excPath, 'utf8'));
  }

  const reportError = (code: string, msg: string) => {
    if (exceptions[code]) {
      console.warn(`WARN: [${job}] ${msg} (Exception: ${exceptions[code]})`);
    } else {
      console.error(`ERROR: [${job}] ${msg}`);
      hasError = true;
    }
  };

  if (sb.shots.length !== spec.scenes.length) {
    reportError('shot_count_mismatch', `Shot count (${sb.shots.length}) does not match scene count (${spec.scenes.length})`);
    return;
  }

  if (sb.shots.length > 0) {
    if (sb.shots[0].role !== 'hook') reportError('first_shot_not_hook', `First shot role is '${sb.shots[0].role}', expected 'hook'`);
    if (sb.shots[sb.shots.length - 1].role !== 'cta') reportError('last_shot_not_cta', `Last shot role is '${sb.shots[sb.shots.length - 1].role}', expected 'cta'`);
  }

  sb.shots.forEach((shot: any, i: number) => {
    const scene = spec.scenes[i];
    
    if (Math.abs(shot.t0 - scene.start) > 0.001) {
      reportError(`t0_mismatch_shot_${i+1}`, `Shot ${i+1} t0 (${shot.t0}) does not match scene start (${scene.start})`);
    }
    const sceneEnd = scene.start + scene.duration;
    if (Math.abs(shot.t1 - sceneEnd) > 0.001) {
      reportError(`t1_mismatch_shot_${i+1}`, `Shot ${i+1} t1 (${shot.t1}) does not match scene end (${sceneEnd})`);
    }

    if ((shot.headline || '') !== (scene.headline || '')) {
      reportError(`headline_mismatch_shot_${i+1}`, `Shot ${i+1} headline mismatch`);
    }
    if ((shot.subline || '') !== (scene.subline || '')) {
      reportError(`subline_mismatch_shot_${i+1}`, `Shot ${i+1} subline mismatch`);
    }
    if ((shot.onScreenText || '') !== (scene.caption || '')) {
      reportError(`text_caption_mismatch_shot_${i+1}`, `Shot ${i+1} onScreenText vs caption mismatch`);
    }
    if ((shot.dialogue || '') !== (scene.vo || '')) {
      reportError(`dialogue_vo_mismatch_shot_${i+1}`, `Shot ${i+1} dialogue vs vo mismatch`);
    }
  });
});

if (hasError) {
  process.exit(1);
} else {
  console.log('Plan vs Spec checks passed.');
}
