import {execFileSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {getJob} from '../jobs/registry';
import {stageJobAssets} from './stage-assets';

const root = process.cwd();
const remotion = resolve(root, 'node_modules', '.bin', process.platform === 'win32' ? 'remotion.cmd' : 'remotion');
const jobId = process.env.AD_JOB_ID ?? process.argv[2] ?? 'swiggy-001';
const job = getJob(jobId);
const outputDir = resolve(root, 'jobs', jobId, 'out', 'stills');
const browser = process.env.REMOTION_BROWSER_EXECUTABLE;
stageJobAssets(root, jobId);
mkdirSync(outputDir, {recursive: true});

const selectedScenes = process.env.SCENE_ID ? job.spec.scenes.filter((scene) => scene.id === process.env.SCENE_ID) : job.spec.scenes;
for (const scene of selectedScenes) {
  const points = [['start', scene.start], ['middle', scene.start + scene.duration / 2], ['end', scene.start + scene.duration - 1 / job.spec.fps] ] as const;
  for (const [label, seconds] of points) {
    const frame = Math.round(seconds * job.spec.fps);
    const output = resolve(outputDir, `${scene.id.toLowerCase()}-${label}.png`);
    console.log(`Rendering ${scene.id} ${label} frame ${frame} -> ${output}`);
    const args = ['still', resolve(root, 'job-entry.tsx'), 'Ad', output, `--frame=${frame}`, '--image-format=png', '--overwrite', '--log=error', '--public-dir', resolve(root, 'public'), '--props', JSON.stringify({jobId})];
    if (browser) args.push(`--browser-executable=${browser}`);
    execFileSync(remotion, args, {stdio: 'inherit', env: {...process.env, AD_JOB_ID: jobId}});
  }
}
