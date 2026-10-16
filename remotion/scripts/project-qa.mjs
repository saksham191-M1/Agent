import {execFileSync, spawnSync} from 'node:child_process';
import {mediaTools} from './media-tools.mjs';

export const verifyProjectExport = (file, expected) => {
  const tools = mediaTools();
  const info = JSON.parse(execFileSync(tools.ffprobe, ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,width,height,pix_fmt,color_range,color_space,color_transfer,color_primaries,r_frame_rate,nb_frames,sample_rate,channels', '-of', 'json', file], {encoding: 'utf8'}));
  const video = info.streams?.find((stream) => stream.codec_type === 'video');
  const audio = info.streams?.find((stream) => stream.codec_type === 'audio');
  const [num, den] = String(video?.r_frame_rate ?? '0/1').split('/').map(Number);
  const duration = Number(info.format?.duration);
  const gates = {
    dimensions: video?.width === expected.width && video?.height === expected.height,
    codec: video?.codec_name === 'h264' && video?.pix_fmt === 'yuv420p',
    color: video?.color_range === 'tv' && video?.color_space === 'bt709'
      && video?.color_transfer === 'bt709' && video?.color_primaries === 'bt709',
    fps: Math.abs(num / den - expected.fps) < .01,
    duration: Number.isFinite(duration) && Math.abs(duration - expected.durationSec) <= Math.max(.12, 2 / expected.fps),
    frames: Number(video?.nb_frames) === Math.round(expected.durationSec * expected.fps),
    audio: expected.audio ? audio?.codec_name === 'aac' && Number(audio.sample_rate) === 48000 && audio.channels === 2 : !audio,
    decode: false,
    sound: !expected.audio,
  };
  // Decode the complete file, not just its container metadata.
  execFileSync(tools.ffmpeg, ['-v', 'error', '-xerror', '-i', file, '-f', 'null', '-'], {stdio: 'pipe', timeout: 120000});
  gates.decode = true;
  let peakDb = null;
  if (audio) {
    const metrics = spawnSync(tools.ffmpeg, ['-hide_banner', '-i', file, '-vn', '-af', 'astats=metadata=0:reset=0', '-f', 'null', '-'], {encoding: 'utf8', timeout: 120000});
    const peaks = [...(metrics.stderr ?? '').matchAll(/Peak level dB:\s*(-?[0-9.]+)/g)].map((match) => Number(match[1]));
    peakDb = peaks.length ? Math.max(...peaks) : null;
    gates.sound = metrics.status === 0 && peakDb !== null && Number.isFinite(peakDb) && peakDb > -60 && peakDb <= .1;
  }
  if (!Object.values(gates).every(Boolean)) throw new Error(`Export QA failed: ${JSON.stringify(gates)}`);
  return {passed: true, gates, media: info, peakDb, metadata: {width: video.width, height: video.height, fps: num / den, duration, audio: Boolean(audio)}};
};
