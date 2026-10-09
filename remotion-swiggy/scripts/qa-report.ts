import {existsSync, mkdirSync, writeFileSync} from 'node:fs';
import {execFileSync, spawnSync} from 'node:child_process';

import {resolve} from 'node:path';
import {getJob, listJobs} from '../jobs/registry';

import {mediaTools} from './media-tools.mjs';
const {ffprobe: ffprobePath, ffmpeg: ffmpegPath} = mediaTools();
const root = process.cwd();
const jobId = process.env.AD_JOB_ID ?? process.argv[2];
if (!jobId) {
  console.error(`Error: Job ID is required.\nAvailable jobs: ${listJobs().join(', ')}`);
  process.exit(1);
}
const job = getJob(jobId);
const outputDir = resolve(root, 'jobs', jobId, 'out');
const final = resolve(outputDir, 'final.mp4');
if (!existsSync(final)) throw new Error(`Missing final render: ${final}`);
mkdirSync(outputDir, {recursive: true});

const dimensions = job.spec.format === '1:1' ? {width: 1080, height: 1080} : job.spec.format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};
const probe = JSON.parse(execFileSync(ffprobePath, [
  '-v', 'error', '-show_entries',
  'format=duration:stream=index,codec_name,codec_type,width,height,pix_fmt,r_frame_rate,sample_rate,channels,bit_rate,color_range,color_space,color_transfer,color_primaries',
  '-of', 'json', final,
], {encoding: 'utf8'}));
const streams = probe.streams ?? [];
const video = streams.find((stream: {codec_type?: string}) => stream.codec_type === 'video');
const audio = streams.find((stream: {codec_type?: string}) => stream.codec_type === 'audio');
const expectedAudio = Boolean(job.spec.audio.music.file || job.spec.audio.room.file || Object.keys(job.spec.audio.voice.clips).length || Object.keys(job.spec.audio.sfxFiles).length);
const expectedDuration = Number(probe.format?.duration);
const actualFps = video?.r_frame_rate ? (() => { const [num, den] = String(video.r_frame_rate).split('/').map(Number); return den ? num / den : 0; })() : 0;
const mediaGate = Boolean(video && video.codec_name === 'h264' && video.width === dimensions.width && video.height === dimensions.height
  && video.pix_fmt === 'yuv420p' && video.color_range === 'tv' && video.color_space === 'bt709' && video.color_transfer === 'bt709' && video.color_primaries === 'bt709'
  && Math.abs(actualFps - job.spec.fps) <= .01 && Number.isFinite(expectedDuration)
  && Math.abs(expectedDuration - job.spec.durationSec) <= Math.max(.08, 2 / job.spec.fps)
  && (!expectedAudio || Boolean(audio && audio.codec_name === 'aac')));

const stills = job.spec.scenes.flatMap((scene) => ['start', 'middle', 'end'].map((point) => resolve(outputDir, 'stills', `${scene.id.toLowerCase()}-${point}.png`)));
const visualGate = stills.every((file) => existsSync(file));
const localAssets = [job.spec.audio.music.file, job.spec.audio.room.file, ...Object.values(job.spec.audio.voice.clips), ...Object.values(job.spec.audio.sfxFiles)]
  .filter(Boolean)
  .map((file) => resolve(root, 'jobs', jobId, 'assets', file));
const assetsGate = localAssets.every((file) => existsSync(file));

const runQa = (filter: string) => {
  if (!audio) return {ok: false, output: 'No audio stream'};
  const nullOutput = process.platform === 'win32' ? 'NUL' : '/dev/null';
  const result = spawnSync(ffmpegPath, ['-hide_banner', '-i', final, '-map', '0:a:0', '-vn', '-af', filter, '-f', 'wav', '-y', nullOutput], {encoding: 'utf8'});
  return {ok: result.status === 0, output: `${result.stdout ?? ''}\n${result.stderr ?? ''}`};
};
const loudness = runQa('ebur128=peak=true:framelog=verbose');
const silence = runQa('silencedetect=noise=-60dB:d=0.3');
// --- Decode to PCM for accurate RMS calculation ---
const pcmProc = spawnSync(ffmpegPath, ['-hide_banner', '-i', final, '-vn', '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'], {encoding: 'buffer', maxBuffer: 10 * 1024 * 1024});
const pcmBuf = pcmProc.stdout;
const sampleRate = 48000;
const windowSamples = sampleRate * 0.5;
const rmsWindows = [];
if (pcmBuf && pcmBuf.length > 0) {
  const totalSamples = pcmBuf.length / 4;
  for (let i = 0; i < totalSamples; i += windowSamples) {
    let sum = 0;
    let count = 0;
    for (let j = 0; j < windowSamples && (i + j) < totalSamples; j++) {
      const v = pcmBuf.readFloatLE((i + j) * 4);
      sum += v * v;
      count++;
    }
    if (count > 0) {
      const rms = Math.sqrt(sum / count);
      rmsWindows.push({time: i / sampleRate, level: rms > 0 ? 20 * Math.log10(rms) : -Infinity});
    }
  }
}
const evaluatedRmsWindows = rmsWindows.filter(w => w.time >= 0.5 && w.time < job.spec.durationSec - 1.5);
const below40 = evaluatedRmsWindows.filter(w => w.level < -40);
const minRmsDbfs = evaluatedRmsWindows.length ? Math.min(...evaluatedRmsWindows.map(w => w.level)) : -Infinity;
const minRmsTime = evaluatedRmsWindows.find(w => w.level === minRmsDbfs)?.time ?? 0;
const rmsGate = minRmsDbfs >= -40;

const hfVol = runQa('highpass=f=4000,volumedetect');
const fullVol = runQa('volumedetect');

const integrated = Number(loudness.output.match(/I:\s+(-?[0-9.]+) LUFS/)?.[1]);
const loudnessRange = Number(loudness.output.match(/LRA:\s+([0-9.]+) LU/)?.[1]);
const truePeak = Number(loudness.output.match(/Peak:\s+(-?[0-9.]+) dBFS/)?.[1]);
const silenceGate = !silence.output.includes('silence_start');

const hfMean = Number(hfVol.output.match(/mean_volume:\s+(-?[0-9.]+) dB/)?.[1] ?? -Infinity);
const fullMean = Number(fullVol.output.match(/mean_volume:\s+(-?[0-9.]+) dB/)?.[1] ?? 0);
const hfEnergyPct = Math.pow(10, (hfMean - fullMean) / 10) * 100;
const hfFormula = '10^((hfMean - fullMean)/10) * 100';

const audioGate = Boolean(audio && loudness.ok && silence.ok && Number.isFinite(integrated) && integrated >= -15 && integrated <= -13
  && Number.isFinite(truePeak) && truePeak <= -1 && Number.isFinite(loudnessRange) && loudnessRange <= 7
  && silenceGate && rmsGate);

const warnings = [];
if (hfEnergyPct < 8) warnings.push(`HF energy is ${hfEnergyPct.toFixed(2)}%, which is below the 8% target for motion jobs.`);

const report = {
  job: jobId,
  durationSec: job.spec.durationSec,
  scenes: job.spec.scenes.length,
  visual: {stillCount: stills.filter((file) => existsSync(file)).length, pointsPerScene: 3},
  media: probe,
  audio: {
    integratedLufs: integrated,
    loudnessRange,
    truePeakDbfs: truePeak,
    silenceGate,
    rmsGate,
    minRmsDbfs,
    minRmsTime,
    hfEnergyPct,
    hfFormula,
    rmsEvaluatedRange: '0.5s to ' + (job.spec.durationSec - 1.5) + 's',
    rmsWindowsBelow40: below40,
    streamPresent: Boolean(audio),
    expected: expectedAudio,
    requiredAssets: localAssets.length,
    assetsPresent: assetsGate,
    sfxCues: job.spec.scenes.reduce((count, scene) => count + scene.sfx.length, 0),
    duckDb: job.spec.audio.duck,
  },
  warnings,
  gates: {
    spec: true,
    renderExists: true,
    media: mediaGate,
    visual: visualGate,
    assets: assetsGate,
    audio: audioGate,
    engineBrandLeak: 'run npm run brand-leak separately',
  },
  claims: job.brand.claims.map((claim) => ({id: claim.id, sourceUrl: claim.sourceUrl})),
};
writeFileSync(resolve(outputDir, 'qa-report.json'), `${JSON.stringify(report, null, 2)}\n`);
console.log(`QA report written to ${resolve(outputDir, 'qa-report.json')}`);
if (!mediaGate || !visualGate || !assetsGate || (expectedAudio && !audioGate)) process.exitCode = 1;
