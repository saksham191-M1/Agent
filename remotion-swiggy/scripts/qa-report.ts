import {existsSync, mkdirSync, writeFileSync} from 'node:fs';
import {execFileSync, spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {getJob} from '../jobs/registry';

const require = createRequire(import.meta.url);
const ffprobePath = require('ffprobe-static').path as string;
const ffmpegPath = require('ffmpeg-static') as string;
const root = process.cwd();
const jobId = process.env.AD_JOB_ID ?? process.argv[2] ?? 'swiggy-001';
const job = getJob(jobId);
const outputDir = resolve(root, 'jobs', jobId, 'out');
const final = resolve(outputDir, 'final.mp4');
if (!existsSync(final)) throw new Error(`Missing final render: ${final}`);
mkdirSync(outputDir, {recursive: true});

const dimensions = job.spec.format === '1:1' ? {width: 1080, height: 1080} : job.spec.format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};
const probe = JSON.parse(execFileSync(ffprobePath, [
  '-v', 'error', '-show_entries',
  'format=duration:stream=index,codec_name,codec_type,width,height,pix_fmt,r_frame_rate,sample_rate,channels,bit_rate',
  '-of', 'json', final,
], {encoding: 'utf8'}));
const streams = probe.streams ?? [];
const video = streams.find((stream: {codec_type?: string}) => stream.codec_type === 'video');
const audio = streams.find((stream: {codec_type?: string}) => stream.codec_type === 'audio');
const expectedAudio = Boolean(job.spec.audio.music.file || job.spec.audio.room.file || Object.keys(job.spec.audio.voice.clips).length || Object.keys(job.spec.audio.sfxFiles).length);
const expectedDuration = Number(probe.format?.duration);
const actualFps = video?.r_frame_rate ? (() => { const [num, den] = String(video.r_frame_rate).split('/').map(Number); return den ? num / den : 0; })() : 0;
const mediaGate = Boolean(video && video.codec_name === 'h264' && video.width === dimensions.width && video.height === dimensions.height
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
const integrated = Number(loudness.output.match(/I:\s+(-?[0-9.]+) LUFS/)?.[1]);
const loudnessRange = Number(loudness.output.match(/LRA:\s+([0-9.]+) LU/)?.[1]);
const truePeak = Number(loudness.output.match(/Peak:\s+(-?[0-9.]+) dBFS/)?.[1]);
const audioGate = Boolean(audio && loudness.ok && silence.ok && Number.isFinite(integrated) && integrated >= -15 && integrated <= -13
  && Number.isFinite(truePeak) && truePeak <= -1 && Number.isFinite(loudnessRange) && loudnessRange <= 7
  && !silence.output.includes('silence_start'));

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
    silenceGate: !silence.output.includes('silence_start'),
    streamPresent: Boolean(audio),
    expected: expectedAudio,
    requiredAssets: localAssets.length,
    assetsPresent: assetsGate,
    sfxCues: job.spec.scenes.reduce((count, scene) => count + scene.sfx.length, 0),
    duckDb: job.spec.audio.duck,
  },
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
