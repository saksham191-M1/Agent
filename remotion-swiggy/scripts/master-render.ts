import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {existsSync, unlinkSync} from 'node:fs';
import {resolve} from 'node:path';
import {getJob} from '../jobs/registry';

const root = process.cwd();
const require = createRequire(import.meta.url);
const ffmpeg = process.env.FFMPEG_PATH ?? require('ffmpeg-static') as string;
const jobId = process.env.AD_JOB_ID ?? process.argv[2] ?? 'swiggy-001';
const job = getJob(jobId);
const raw = resolve(root, 'jobs', jobId, 'out', 'raw.mp4');
const final = resolve(root, 'jobs', jobId, 'out', 'final.mp4');

if (!existsSync(raw)) throw new Error(`Missing raw render: ${raw}`);
if (existsSync(final)) unlinkSync(final);

execFileSync(ffmpeg, [
  '-hide_banner', '-i', raw,
  '-map', '0:v:0', '-map', '0:a:0',
  '-c:v', 'copy',
  '-af', 'loudnorm=I=-14:TP=-1:LRA=7',
  '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2',
   '-t', String(job.spec.durationSec),
  '-movflags', '+faststart', '-y', final,
], {stdio: 'inherit'});

console.log(`Mastered render written to ${final}`);
