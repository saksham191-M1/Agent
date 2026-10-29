import {execFileSync} from 'node:child_process';

import {existsSync, unlinkSync} from 'node:fs';
import {resolve} from 'node:path';
import {getJob, listJobs} from '../jobs/registry';

const root = process.cwd();
import {mediaTools} from './media-tools.mjs';
import {validateJob} from './lib/job-guard';

const {ffmpeg} = mediaTools();
const isForce = process.argv.includes('--force');
const jobId = process.env.AD_JOB_ID ?? process.argv.find(a => !a.startsWith('--') && a !== process.argv[0] && a !== process.argv[1]);
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
    console.error(`\n❌ [JOB GUARD FAILED] Cannot master ${jobId}:`);
    for (const err of guardResult.errors) {
      console.error(`  - [${err.code}] ${err.message}`);
    }
    console.error(`Use --force to downgrade errors to warnings (debugging only).\n`);
    process.exit(1);
  }
}
const job = getJob(jobId);
const raw = resolve(root, 'jobs', jobId, 'out', 'raw.mp4');
const final = resolve(root, 'jobs', jobId, 'out', 'final.mp4');

if (!existsSync(raw)) throw new Error(`Missing raw render: ${raw}`);
if (existsSync(final)) unlinkSync(final);

execFileSync(ffmpeg, [
  '-hide_banner', '-i', raw,
  '-map', '0:v:0', '-map', '0:a:0',
  '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p',
  '-vf', 'colorspace=range=tv:irange=pc:all=bt709:iall=bt709:fast=1',
  '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
  '-bsf:v', 'h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1',
  '-af', 'loudnorm=I=-14:TP=-1.5:LRA=7',
  '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2',
   '-t', String(job.spec.durationSec),
  '-movflags', '+faststart', '-y', final,
], {stdio: 'inherit'});

console.log(`Mastered render written to ${final}`);
