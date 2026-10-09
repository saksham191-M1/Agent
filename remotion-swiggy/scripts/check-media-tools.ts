import {readFileSync, readdirSync, statSync} from 'node:fs';
import {join} from 'node:path';

function walk(dir: string): string[] {
  let results: string[] = [];
  const list = readdirSync(dir);
  for (const file of list) {
    const p = join(dir, file);
    if (statSync(p).isDirectory()) {
      results = results.concat(walk(p));
    } else {
      if (p.endsWith('.ts') || p.endsWith('.js') || p.endsWith('.mjs') || p.endsWith('.tsx')) {
        results.push(p);
      }
    }
  }
  return results;
}

let failed = false;
const files = walk('scripts');
for (const file of files) {
  if (file.includes('media-tools.mjs') || file.includes('check-media-tools')) continue;
  const content = readFileSync(file, 'utf-8');
  if (content.includes('ffmpeg-static') || content.includes('ffprobe-static')) {
    console.error(`Error: Direct import of ffmpeg-static/ffprobe-static found in ${file}. Use media-tools.mjs instead.`);
    failed = true;
  }
}
if (failed) process.exit(1);
