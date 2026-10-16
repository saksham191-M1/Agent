import {SfxBeatEngineV2} from '../engine/audio/sfx-beat-engine-v2';

const arg = process.argv[2];
const duration = arg ? parseFloat(arg) : 12;

if (isNaN(duration) || duration <= 0) {
  console.error('Usage: tsx scripts/sfx-map.ts <durationInSeconds>');
  process.exit(1);
}

const map = SfxBeatEngineV2.formatOutput(duration);
console.log(map);
