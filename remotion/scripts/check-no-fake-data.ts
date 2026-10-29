import {readFileSync, readdirSync, statSync} from 'node:fs';
import {resolve, relative} from 'node:path';

/**
 * check-no-fake-data.ts
 * ─────────────────────
 * Lint-style test verifying that hardcoded fake fallback data (such as fake prices,
 * fake ratings, and generic PAS fallback copy) never exists in the codebase.
 */

const root = process.cwd();
const dirsToScan = [
  resolve(root, 'engine'),
  resolve(root, 'scripts'),
  resolve(root, 'jobs'),
];

// Literal strings banned by Phase 1
const BANNED_PATTERNS: Array<{pattern: RegExp; description: string}> = [
  {pattern: /₹?1,499/i, description: 'Hardcoded price ₹1,499'},
  {pattern: /₹?4,999/i, description: 'Hardcoded original price ₹4,999'},
  {pattern: /48,200\+/i, description: 'Hardcoded rating count 48,200+'},
  {pattern: /7\s*days\s*easy\s*replacement/i, description: 'Hardcoded 7 Days easy replacement policy'},
  {pattern: /The problem \$\{brand\.name\} solves/i, description: 'Hardcoded PAS fallback copy'},
];

const selfPath = resolve(root, 'scripts', 'check-no-fake-data.ts');
const files: string[] = [];

function walk(dir: string): void {
  for (const entry of readdirSync(dir)) {
    const fullPath = resolve(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      if (entry !== 'node_modules' && entry !== '.git' && entry !== 'out' && entry !== 'dist') {
        walk(fullPath);
      }
    } else if (/\.(ts|tsx|js|mjs|json)$/.test(entry) && fullPath !== selfPath) {
      files.push(fullPath);
    }
  }
}

for (const dir of dirsToScan) {
  walk(dir);
}

let violationsCount = 0;

for (const file of files) {
  const content = readFileSync(file, 'utf8');
  for (const {pattern, description} of BANNED_PATTERNS) {
    if (pattern.test(content)) {
      console.error(`[check-no-fake-data] ❌ BANNED LITERAL FOUND: ${description} in ${relative(root, file)}`);
      violationsCount++;
    }
  }
}

if (violationsCount > 0) {
  console.error(`\n[check-no-fake-data] ❌ ${violationsCount} banned literal string violation(s) detected.`);
  process.exitCode = 1;
} else {
  console.log(`[check-no-fake-data] ✅ Passed. Scanned ${files.length} files. Zero fake data literals found.`);
}
