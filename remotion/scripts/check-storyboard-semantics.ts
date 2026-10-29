import {readFileSync, existsSync} from 'node:fs';
import {resolve, basename, dirname} from 'node:path';

const file = process.argv[2];
if (!file) {
  console.error("Usage: tsx scripts/check-storyboard-semantics.ts <storyboard.json>");
  process.exit(1);
}

const isJsonPath = file.endsWith('.json');
const jobId = isJsonPath ? basename(dirname(resolve(process.cwd(), file))) : file;
const actualFile = file.endsWith('.json') ? resolve(process.cwd(), file) : resolve(process.cwd(), 'jobs', file, 'storyboard.json');

const data = JSON.parse(readFileSync(actualFile, 'utf8'));
const shots = data.shots || [];

const errors: string[] = [];
const warnings: string[] = [];
const usedExceptions = new Set<string>();

let knownExceptions: Record<string, string> = {};
const exceptionsPath = resolve(process.cwd(), 'jobs', jobId, 'known-exceptions.json');
if (existsSync(exceptionsPath)) {
  try {
    const rawParsed = JSON.parse(readFileSync(exceptionsPath, 'utf8'));
    if (Array.isArray(rawParsed)) {
      for (const item of rawParsed) {
        if (item && item.rule) {
          knownExceptions[item.rule] = item.reason || 'waiver';
        }
      }
    } else if (typeof rawParsed === 'object' && rawParsed !== null) {
      knownExceptions = rawParsed as Record<string, string>;
    }
  } catch (e: unknown) {
    console.warn(`[${jobId}] WARN: Failed to parse known-exceptions.json - ${e instanceof Error ? e.message : String(e)}`);
  }
}

const reportIssue = (msg: string, code: string) => {
  const fullMsg = `[${jobId}] ${msg}`;
  if (code in knownExceptions) {
    usedExceptions.add(code);
    warnings.push(fullMsg + ` (Exception: ${knownExceptions[code]})`);
  } else {
    errors.push(fullMsg);
  }
};

interface Shot {
  n: number;
  t0: number;
  t1: number;
  role: string;
  dialogue?: string;
  headline?: string;
  subline?: string;
  onScreenText?: string;
  visual?: unknown;
  camera?: unknown;
  transitionOut?: unknown;
}

shots.forEach((shot: Shot, i: number) => {
  if (shot.t1 - shot.t0 > 5) reportIssue(`Shot ${shot.n} length > 5s`, 'length_exceeded');
  if (shot.t0 >= shot.t1) reportIssue(`Shot ${shot.n} t0 >= t1`, 'invalid_timing');
  if (i > 0) {
    const prev = shots[i - 1];
    if (Math.abs(shot.t0 - prev.t1) > 0.001) reportIssue(`Shot ${shot.n} t0 does not match previous t1`, 'non_contiguous');
  }
  if (shot.n !== i + 1) reportIssue(`Shot ${shot.n} is not sequential (expected ${i + 1})`, 'non_sequential');
  
  if (shot.dialogue) {
    const words = shot.dialogue.split(/\s+/).filter(Boolean).length;
    const duration = shot.t1 - shot.t0;
    if (words / duration > 2.5 + 1e-6) reportIssue(`Shot ${shot.n} dialogue exceeds 2.5 words/sec`, `dialogue_speed_shot_${shot.n}`);
  }

  const wordCount = (str?: string) => str ? str.split(/\s+/).filter(Boolean).length : 0;
  if (wordCount(shot.onScreenText) > 6) reportIssue(`Shot ${shot.n} onScreenText exceeds 6 words`, `onscreen_len_shot_${shot.n}`);
  if (wordCount(shot.headline) > 8) reportIssue(`Shot ${shot.n} headline exceeds 8 words`, `headline_len_shot_${shot.n}`);
  if (wordCount(shot.subline) > 12) reportIssue(`Shot ${shot.n} subline exceeds 12 words`, `subline_len_shot_${shot.n}`);
  
  if (shot.role === 'hook') {
    if (shot.t0 !== 0) reportIssue(`Shot ${shot.n} (hook) does not start at 0`, 'hook_start');
    if (shot.t1 > 2) reportIssue(`Shot ${shot.n} (hook) ends after 2s`, `hook_length_shot_${shot.n}`);
  }
  
  const texts = [shot.headline, shot.subline, shot.onScreenText].filter(Boolean);
  const uniqueTexts = new Set(texts);
  if (texts.length !== uniqueTexts.size) reportIssue(`Shot ${shot.n} has duplicated copy`, `duplicate_copy_shot_${shot.n}`);
  
  if (i > 0) {
    const prev = shots[i - 1];
    const stringify = (s: Shot) => JSON.stringify({v: s.visual, c: s.camera, t: s.transitionOut});
    if (stringify(shot) === stringify(prev)) reportIssue(`Shot ${shot.n} has identical visual+camera+transition to previous`, 'consecutive_identical');
  }
});

for (const code of Object.keys(knownExceptions)) {
  if (!usedExceptions.has(code)) {
    console.warn(`[${jobId}] WARN: Unknown or unused exception code in known-exceptions.json: ${code}`);
  }
}

if (warnings.length > 0) {
  console.warn("Semantic warnings (known exceptions):");
  warnings.forEach(w => console.warn(" WARN: " + w));
}

if (errors.length > 0) {
  console.error("Semantic errors found:");
  errors.forEach(e => console.error(" ERROR: " + e));
  process.exit(1);
}

console.log(`[${jobId}] Storyboard semantic rules passed.`);
