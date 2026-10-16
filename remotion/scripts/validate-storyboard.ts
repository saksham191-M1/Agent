import Ajv from 'ajv';
import {readFileSync} from 'node:fs';
import {resolve, extname} from 'node:path';
import {spawnSync} from 'node:child_process';

const root = process.cwd();
const ajv = new Ajv();
const schema = JSON.parse(readFileSync(resolve(root, 'engine/storyboard.schema.json'), 'utf8'));
const validate = ajv.compile(schema);

const target = process.argv[2];
const { listJobs } = require('../jobs/registry');

let jobsToTest: string[] = [];
let targetIsFile = false;

if (target) {
  if (extname(target) === '.json') {
    targetIsFile = true;
    jobsToTest = [target];
  } else {
    jobsToTest = [target];
  }
} else {
  jobsToTest = listJobs();
}

let failed = false;
for (const item of jobsToTest) {
  const filePath = targetIsFile ? resolve(root, item) : resolve(root, 'jobs', item, 'storyboard.json');
  let data;
  try {
    data = JSON.parse(readFileSync(filePath, 'utf8'));
  } catch (e: any) {
    console.error(`Failed to read or parse storyboard for ${item}: ${e.message}`);
    failed = true;
    continue;
  }
  
  if (!validate(data)) {
    console.error(`Schema validation failed for ${item}:`, validate.errors);
    failed = true;
  }
  
  const semantic = spawnSync('node', ['node_modules/tsx/dist/cli.mjs', 'scripts/check-storyboard-semantics.ts', filePath], {stdio: 'inherit'});
  if (semantic.error) {
    console.error(`Failed to run semantic check: ${semantic.error.message}`);
    failed = true;
  } else if (semantic.status !== 0) {
    failed = true;
  }
}

if (failed) {
  process.exit(1);
}
console.log('Storyboard schema valid.');
