import {spawnSync} from 'node:child_process';
import {listJobs} from '../jobs/registry';

const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}

console.log(`Starting studio for ${jobId}...`);
const studio = spawnSync('npx', ['remotion', 'studio', 'job-entry.tsx', '--props', JSON.stringify({jobId})], {stdio: 'inherit'});
if (studio.status !== 0) process.exit(studio.status ?? 1);
