import {readFileSync, readdirSync, statSync} from 'node:fs';
import {resolve} from 'node:path';

const root = process.cwd();
const jobsRoot = resolve(root, 'jobs');
const engineRoot = resolve(root, 'engine');
const terms = new Set<string>();
const colors = new Set<string>();
for (const job of readdirSync(jobsRoot, {withFileTypes: true}).filter((entry) => entry.isDirectory())) {
  const brand = JSON.parse(readFileSync(resolve(jobsRoot, job.name, 'brand.json'), 'utf8'));
  terms.add(String(brand.name).toLowerCase());
  for (const product of brand.products ?? []) terms.add(String(product).toLowerCase());
  for (const color of Object.values(brand.colors ?? {})) {
    if (typeof color === 'string' && /^#[0-9a-f]{3,8}$/i.test(color)) {
      const lower = color.toLowerCase();
      if (lower !== '#ffffff' && lower !== '#000000') colors.add(lower);
    }
  }
}
const files: string[] = [];
const walk = (dir: string) => { for (const entry of readdirSync(dir)) { const path = resolve(dir, entry); if (statSync(path).isDirectory()) walk(path); else if (/\.(ts|tsx|json|md)$/.test(entry)) files.push(path); } };
walk(engineRoot);
let failed = false;
for (const file of files) {
  const text = readFileSync(file, 'utf8').toLowerCase();
  for (const term of [...terms, ...colors]) if (text.includes(term)) { failed = true; console.error(`Brand literal in engine: ${file} -> ${term}`); }
}
if (failed) process.exitCode = 1;
else console.log(`Brand-leak check passed: ${files.length} engine files scanned.`);
