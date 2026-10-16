import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';
import {stageJobAssets} from './stage-assets';
import {listJobs} from '../jobs/registry';

const root = process.cwd();
const remotionPath = resolve(root, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}
const output = resolve(root, 'jobs', jobId, 'out', 'raw.mp4');
const browser = process.env.REMOTION_BROWSER_EXECUTABLE;
stageJobAssets(root, jobId);

const args = [
  'render',
  resolve(root, 'job-entry.tsx'),
  'Ad',
  output,
  '--codec=h264',
  '--crf=16',
  '--pixel-format=yuv420p',
  '--audio-codec=aac',
  '--audio-bitrate=256k',
  '--log=error',
  '--public-dir',
  resolve(root, 'public'),
  '--bundle-cache=false',
  '--props',
  JSON.stringify({jobId}),
];

if (browser) args.push(`--browser-executable=${browser}`);

execFileSync(process.execPath, [remotionPath, ...args], {
  stdio: 'inherit',
  env: {...process.env, AD_JOB_ID: jobId}
});
