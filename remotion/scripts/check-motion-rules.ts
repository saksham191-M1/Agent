import {readFileSync, existsSync} from 'node:fs';
import {resolve, basename, dirname} from 'node:path';
import {validateMotionRules, MOTION_RULES} from '../engine/motion/motion-rules';
import type {AdSpec} from '../engine/types';

const target = process.argv[2] || 'instagram-001';

const isJsonPath = target.endsWith('.json');
const jobId = isJsonPath ? basename(dirname(resolve(process.cwd(), target))) : target;
const actualFile = isJsonPath
  ? resolve(process.cwd(), target)
  : resolve(process.cwd(), 'jobs', target, 'spec.json');

if (!existsSync(actualFile)) {
  console.error(`❌ [${jobId}] spec.json not found at: ${actualFile}`);
  process.exit(1);
}

console.log(`\n🔍 Validating motion rules for: ${jobId} (Rules v${MOTION_RULES.version})`);

try {
  const spec: AdSpec = JSON.parse(readFileSync(actualFile, 'utf8'));
  const result = validateMotionRules(spec);

  if (!result.valid) {
    console.error(`\n❌ Motion rules validation FAILED with ${result.violations.length} violations:`);
    result.violations.forEach((violation, i) => {
      console.error(`   ${i + 1}. ${violation}`);
    });
    process.exit(1);
  }

  console.log(`✅ [${jobId}] All motion rules satisfied! (FPS: ${spec.fps}, Transitions & Easing clean, 0 banned patterns)`);
} catch (err) {
  console.error(`❌ Failed to validate motion rules:`, err);
  process.exit(1);
}
