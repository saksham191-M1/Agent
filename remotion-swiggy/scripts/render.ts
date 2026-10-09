import {spawnSync} from 'node:child_process';
import {listJobs} from '../jobs/registry';

const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}

console.log(`Running render for ${jobId}...`);
const raw = spawnSync('npm', ['run', 'render:job', '--', jobId], {stdio: 'inherit'});
if (raw.status !== 0) process.exit(raw.status ?? 1);

const master = spawnSync('npm', ['run', 'master:job', '--', jobId], {stdio: 'inherit'});
if (master.status !== 0) process.exit(master.status ?? 1);
