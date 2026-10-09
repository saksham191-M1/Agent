import {execFileSync} from 'node:child_process';
import {mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {getJob} from '../jobs/registry';
import {stageJobAssets} from './stage-assets';
import {listJobs} from '../jobs/registry';

const root = process.cwd();
const remotionPath = resolve(root, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}
const job = getJob(jobId);
const outputDir = resolve(root, 'jobs', jobId, 'out', 'stills');
const browser = process.env.REMOTION_BROWSER_EXECUTABLE;
stageJobAssets(root, jobId);
mkdirSync(outputDir, {recursive: true});

const specArg = process.argv.find(a => a.startsWith('--spec='));
const customSpecPath = specArg ? resolve(root, specArg.split('=')[1]) : null;
const specObj = customSpecPath ? JSON.parse(require('node:fs').readFileSync(customSpecPath, 'utf8')) : null;
const activeSpec = specObj || job.spec;

const selectedScenes = process.env.SCENE_ID ? activeSpec.scenes.filter((scene: any) => scene.id === process.env.SCENE_ID) : activeSpec.scenes;
for (const scene of selectedScenes) {
  const points = [['middle', scene.start + scene.duration / 2]] as const;
  for (const [label, seconds] of points) {
    const frame = Math.round(seconds * activeSpec.fps);
    const prefix = customSpecPath ? 'compiled' : 'original';
    const output = resolve(outputDir, `${scene.id.toLowerCase()}-${label}-${prefix}.png`);
    console.log(`Rendering ${scene.id} ${label} frame ${frame} (${prefix}) -> ${output}`);
    const props = specObj ? {jobId, customSpec: specObj} : {jobId};
    const args = ['still', resolve(root, 'job-entry.tsx'), 'Ad', output, `--frame=${frame}`, '--image-format=png', '--overwrite', '--log=error', '--public-dir', resolve(root, 'public'), '--props', JSON.stringify(props)];
    if (browser) args.push(`--browser-executable=${browser}`);
    execFileSync(process.execPath, [remotionPath, ...args], {stdio: 'inherit', env: {...process.env, AD_JOB_ID: jobId}});
  }
}
