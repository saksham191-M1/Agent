/**
 * audio-spec.ts
 * ─────────────
 * Builds the isolated AudioSpec for a job, copying the neutral default audio pack
 * into jobs/<jobId>/assets/audio, selecting music bed by mood, and establishing
 * proper self-contained assetsRoot paths.
 */

import fs from 'node:fs';
import path from 'node:path';

export interface BuildAudioSpecOptions {
  jobId: string;
  musicMood?: string;
  category?: string;
  silentVo?: boolean;
}

export function resolveMusicBedFile(musicMood?: string, category?: string): string {
  const mood = (musicMood || '').toLowerCase();
  const cat = (category || '').toLowerCase();

  // High energy / delivery / e-commerce / mobile apps
  if (/high_energy|upbeat|fast|intense|hype/.test(mood) || cat === 'mobile_app' || cat === 'ecommerce') {
    return 'bed-upbeat-electronic.mp3';
  }
  // Corporate / fintech / trading / analytics
  if (/calm|minimal|serene|precise|corporate/.test(mood) || cat === 'analytics') {
    return 'bed-corporate-minimal.mp3';
  }
  // Lo-Fi / SaaS / dev tools / AI
  if (/lofi|chill|agent|dev|modern/.test(mood) || cat === 'dev_tool' || cat === 'ai_agent') {
    return 'bed-modern-lofi.mp3';
  }
  // Default cinematic
  return 'bed-cinematic-pulse.mp3';
}

export function buildAudioSpec(options: BuildAudioSpecOptions): any {
  const {jobId, musicMood, category, silentVo = false} = options;
  const projectRoot = path.resolve(process.cwd(), '..');
  const defaultPackDir = path.resolve(projectRoot, 'assets', 'default', 'audio');
  const bedsDir = path.resolve(defaultPackDir, 'beds');
  const jobAssetsAudio = path.resolve(process.cwd(), 'jobs', jobId, 'assets', 'audio');

  fs.mkdirSync(jobAssetsAudio, {recursive: true});

  // Copy neutral SFX and room-tone if present
  if (fs.existsSync(defaultPackDir)) {
    const files = fs.readdirSync(defaultPackDir);
    for (const f of files) {
      if (f === 'beds') continue;
      const dest = path.join(jobAssetsAudio, f);
      if (!fs.existsSync(dest)) {
        fs.copyFileSync(path.join(defaultPackDir, f), dest);
      }
    }
  }

  // Resolve and copy categorical music bed
  const bedFilename = resolveMusicBedFile(musicMood, category);
  const bedSource = path.join(bedsDir, bedFilename);
  const bedDest = path.join(jobAssetsAudio, 'music-bed.mp3');

  if (fs.existsSync(bedSource)) {
    fs.copyFileSync(bedSource, bedDest);
    console.log(`[Audio Spec] 🎵 Categorical music bed assigned: ${bedFilename} (mood: ${musicMood || 'default'}, category: ${category || 'general'})`);
  } else if (!fs.existsSync(bedDest) && fs.existsSync(path.join(defaultPackDir, 'music-bed.mp3'))) {
    fs.copyFileSync(path.join(defaultPackDir, 'music-bed.mp3'), bedDest);
  }

  const sfxList = ['click.wav', 'pop.wav', 'pop2.wav', 'tick.wav', 'whoosh.wav', 'swipe.wav', 'thud.wav', 'riser.wav', 'success.wav', 'logo-sting.wav']
    .filter(f => fs.existsSync(path.join(jobAssetsAudio, f)));

  return {
    assetsRoot: `jobs/${jobId}/assets`,
    music: {
      file: 'audio/music-bed.mp3',
      volume: 0.18,
      ducking: true
    },
    roomTone: {
      file: 'audio/room-tone.wav',
      volume: 0.05
    },
    sfxFiles: sfxList.map(f => `audio/${f}`),
    voiceClips: [],
    silentVo
  };
}
