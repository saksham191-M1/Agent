import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

const jobId = process.argv[2];
const file = resolve(process.cwd(), 'jobs', jobId, 'out', 'final.mp4');

let output = '';
try {
  execFileSync('ffmpeg', [
    '-i', file,
    '-af', 'asetnsamples=4800,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level',
    '-f', 'null', '-'
  ], {
    stdio: ['pipe', 'pipe', 'pipe'],
    encoding: 'utf8'
  });
} catch (e: any) {
  output = e.stderr.toString();
}

const lines = output.split('\n');
const vals: {t: number, m: number}[] = [];
let currentTime = 0;

for (const line of lines) {
  if (line.includes('pts_time:')) {
    const m = line.match(/pts_time:([\d.]+)/);
    if (m) currentTime = parseFloat(m[1]);
  }
  if (line.includes('lavfi.astats.Overall.RMS_level=')) {
    const m = line.match(/lavfi.astats.Overall.RMS_level=([-\d.]+)/);
    if (m) {
      const level = parseFloat(m[1]);
      vals.push({t: currentTime, m: level});
    }
  }
}

const targets = [3.5, 6.0, 6.5, 9.0, 11.5, 12.0, 12.5, 17.5, 18.0];
targets.forEach(t => {
  const windowVals = vals.filter(v => v.t >= t && v.t < t + 0.5);
  let minLevel = 0;
  if (windowVals.length > 0) {
    minLevel = Math.min(...windowVals.map(v => v.m));
  }
  console.log(`[${t.toFixed(1)}s] -> After RMS: ${minLevel.toFixed(2)} dBFS`);
});
