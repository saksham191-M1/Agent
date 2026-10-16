import {createHash} from 'node:crypto';
import {readdirSync, readFileSync, statSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

import {listJobs} from '../jobs/registry';

const root = process.cwd();
const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}
const files: string[] = [];
const walk = (dir: string) => { for (const entry of readdirSync(dir)) { const path = resolve(dir, entry); if (statSync(path).isDirectory()) walk(path); else files.push(path); } };
walk(resolve(root, 'engine'));
files.sort();
const hash = createHash('sha256');
for (const file of files) {
  hash.update(file.slice(root.length).replace(/\\/g, '/'));
  hash.update(Buffer.from(readFileSync(file, 'utf8').replace(/\r\n/g, '\n')));
}
const fingerprint = hash.digest('hex');
const output = resolve(root, 'jobs', jobId, 'out', 'engine-fingerprint.txt');
writeFileSync(output, `${fingerprint}\n`);
console.log(`${jobId}: ${fingerprint}`);
