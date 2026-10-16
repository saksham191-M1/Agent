import {spawnSync} from 'node:child_process';
import {writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const jobId = process.argv[2];
if (!jobId) {
  console.error("Usage: tsx scripts/range-test.ts <jobId>");
  process.exit(1);
}

const run = (cmd: string, args: string[]) => {
  const p = spawnSync(cmd, args, {encoding: 'utf8'});
  return (p.stdout || '') + '\n' + (p.stderr || '');
};

const root = process.cwd();
const rawPath = `jobs/${jobId}/out/raw.mp4`;
const finalPath = `jobs/${jobId}/out/final.mp4`;
const logPath = resolve(root, 'docs', 'reports', 'logs', `08-range-raw.txt`);

let out = '';
out += '=== RAW RAMP ===\n';
out += run('ffprobe', ['-f', 'lavfi', '-i', 'movie=out/raw_ramp.mp4,select=\'eq(n\\,10)\',signalstats', '-show_entries', 'frame_tags=lavfi.signalstats.YMIN,lavfi.signalstats.YMAX', '-v', '0', '-of', 'default=noprint_wrappers=1:nokey=1']);

out += '=== MASTER RAMP ===\n';
out += run('ffprobe', ['-f', 'lavfi', '-i', 'movie=out/master_ramp.mp4,select=\'eq(n\\,10)\',signalstats', '-show_entries', 'frame_tags=lavfi.signalstats.YMIN,lavfi.signalstats.YMAX', '-v', '0', '-of', 'default=noprint_wrappers=1:nokey=1']);

out += `=== ${jobId} RAW FRAME 150 ===\n`;
out += run('ffprobe', ['-f', 'lavfi', '-i', `movie=${rawPath},select='eq(n\\,150)',signalstats`, '-show_entries', 'frame_tags=lavfi.signalstats.YMIN,lavfi.signalstats.YMAX', '-v', '0', '-of', 'default=noprint_wrappers=1:nokey=1']);

out += `=== ${jobId} FINAL FRAME 150 ===\n`;
out += run('ffprobe', ['-f', 'lavfi', '-i', `movie=${finalPath},select='eq(n\\,150)',signalstats`, '-show_entries', 'frame_tags=lavfi.signalstats.YMIN,lavfi.signalstats.YMAX', '-v', '0', '-of', 'default=noprint_wrappers=1:nokey=1']);

writeFileSync(logPath, out);
console.log(`Wrote range test results to ${logPath}`);
