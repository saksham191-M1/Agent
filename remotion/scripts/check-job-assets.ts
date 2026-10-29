import {existsSync, readFileSync, readdirSync} from 'node:fs';
import {join, resolve} from 'node:path';

type Claim = {id?: string; label?: string; value?: string; sourceUrl?: string};

const root = process.cwd();
const only = process.argv[2];
const jobsDir = join(root, 'jobs');
const jobs = only
  ? [only]
  : readdirSync(jobsDir, {withFileTypes: true}).filter((d) => d.isDirectory()).map((d) => d.name);

let totalErrors = 0;
let totalWarnings = 0;

const isHomepageOnly = (url: string): boolean => {
  try {
    const u = new URL(url);
    return u.pathname === '/' || u.pathname === '';
  } catch {
    return true;
  }
};

for (const job of jobs) {
  const brandPath = join(jobsDir, job, 'brand.json');
  if (!existsSync(brandPath)) continue;
  const errors: string[] = [];
  const warnings: string[] = [];
  const brand = JSON.parse(readFileSync(brandPath, 'utf8'));

  const src: string | undefined = brand.logo?.src;
  if (src) {
    const clean = src.replace(/^\//, '');
    const found = [resolve(root, clean), resolve(root, 'public', clean), resolve(jobsDir, job, clean)].some(existsSync);
    if (!found) errors.push(`logo.src "${src}" does not exist (looked in project root, public/ and the job folder).`);
  }

  (brand.claims as Claim[] | undefined)?.forEach((c) => {
    const name = c.id || c.label || '(unnamed claim)';
    if (!c.value) errors.push(`claim "${name}" has no value.`);
    if (!c.sourceUrl) errors.push(`claim "${name}" has no sourceUrl.`);
    else if (isHomepageOnly(c.sourceUrl)) warnings.push(`claim "${name}" cites only a homepage (${c.sourceUrl}); link the page that states it.`);
    if (c.value && !/\d/.test(c.value)) warnings.push(`claim "${name}" value "${c.value}" is not a number; it will not read as a metric.`);
  });

  if (errors.length || warnings.length) {
    console.log(`\n[${job}]`);
    errors.forEach((e) => console.log(`  ERROR   ${e}`));
    warnings.forEach((w) => console.log(`  WARNING ${w}`));
  }
  totalErrors += errors.length;
  totalWarnings += warnings.length;
}

console.log(`\nAsset check: ${totalErrors} error(s), ${totalWarnings} warning(s) across ${jobs.length} job(s).`);
if (only && totalErrors > 0) process.exit(1);
