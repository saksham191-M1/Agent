/**
 * job-check.ts
 * ────────────
 * CLI for running validateJob on a specific job or all jobs.
 *
 * Usage:
 *   npx tsx scripts/job-check.ts zomato-001
 *   npx tsx scripts/job-check.ts --all
 */

import path from 'node:path';
import {validateJob} from './lib/job-guard';
import {listJobs} from '../jobs/registry';

const jobsRoot = path.resolve(process.cwd(), 'jobs');
const target = process.argv[2];

if (!target) {
  console.error('Usage: npx tsx scripts/job-check.ts <jobId> | --all');
  process.exit(1);
}

const jobsToCheck = target === '--all' ? listJobs() : [target];
let hasFailure = false;

for (const jobId of jobsToCheck) {
  console.log(`\n🔍 Checking job: ${jobId}`);
  const res = validateJob(jobsRoot, jobId);

  if (res.warnings.length > 0) {
    console.log(`  ⚠️ Warnings (${res.warnings.length}):`);
    for (const w of res.warnings) {
      console.log(`    - [${w.code}] ${w.message}`);
    }
  }

  if (res.errors.length > 0) {
    hasFailure = true;
    console.error(`  ❌ Errors (${res.errors.length}):`);
    for (const err of res.errors) {
      console.error(`    - [${err.code}] ${err.message}`);
    }
  } else {
    console.log(`  ✅ Passed all job guard checks.`);
  }
}

if (hasFailure) {
  process.exit(1);
} else {
  process.exit(0);
}
