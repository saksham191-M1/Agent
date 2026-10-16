import fs from 'node:fs';
import path from 'node:path';

type AudioFile = {
  name: string;
  category: 'master_mix' | 'sync_test' | 'sfx_library' | 'artifact';
  sizeBytes: number;
  uri: string;
  localPath: string;
};

const audioExtensions = new Set(['.wav', '.mp3', '.aac', '.m4a']);
const results: AudioFile[] = [];

function scanDirectory(dir: string, category: AudioFile['category']) {
  if (!fs.existsSync(dir)) return;
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && entry.name !== 'node_modules' && entry.name !== '.git') {
      scanDirectory(full, category);
    } else if (entry.isFile() && audioExtensions.has(path.extname(entry.name).toLowerCase())) {
      const stats = fs.statSync(full);
      const normalizedPath = full.replace(/\\/g, '/');
      results.push({
        name: entry.name,
        category,
        sizeBytes: stats.size,
        uri: `file:///${normalizedPath.replace(/^\/?/, '')}`,
        localPath: normalizedPath,
      });
    }
  }
}

// 1. Scan output directories
scanDirectory(path.resolve('out'), 'sync_test');

// 2. Scan jobs directories
scanDirectory(path.resolve('jobs'), 'master_mix');

// 3. Scan artifact directory
scanDirectory('C:/Users/hemam/.gemini/antigravity/brain/3c4eb451-d156-463b-b133-6448310f27b8', 'artifact');

console.log(JSON.stringify(results, null, 2));
