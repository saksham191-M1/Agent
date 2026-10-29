import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';
import {stageJobAssets} from './stage-assets';
import {listJobs} from '../jobs/registry';
import {validateJob} from './lib/job-guard';

const root = process.cwd();
const remotionPath = resolve(root, 'node_modules', '@remotion', 'cli', 'remotion-cli.js');
const isForce = process.argv.includes('--force');
let jobId = process.env.AD_JOB_ID;
if (!jobId) {
  const jobIdx = process.argv.indexOf('--job');
  if (jobIdx !== -1 && process.argv[jobIdx + 1]) {
    jobId = process.argv[jobIdx + 1];
  } else {
    jobId = process.argv.find(a => !a.startsWith('--') && a !== process.argv[0] && a !== process.argv[1]);
  }
}
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}

// Job Guard check
const guardResult = validateJob(resolve(root, 'jobs'), jobId);
if (!guardResult.valid) {
  if (isForce) {
    console.warn(`\n⚠️  [JOB GUARD WARNING] Proceeding due to --force flag:`);
    for (const err of guardResult.errors) {
      console.warn(`  - [${err.code}] ${err.message}`);
    }
  } else {
    console.error(`\n❌ [JOB GUARD FAILED] Cannot render ${jobId}:`);
    for (const err of guardResult.errors) {
      console.error(`  - [${err.code}] ${err.message}`);
    }
    console.error(`Use --force to downgrade errors to warnings (debugging only).\n`);
    process.exit(1);
  }
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
