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
  silentVo?: boolean;
}

export function buildAudioSpec(options: BuildAudioSpecOptions): any {
  const {jobId, silentVo = false} = options;
  const projectRoot = path.resolve(process.cwd(), '..');
  const defaultPackDir = path.resolve(projectRoot, 'assets', 'default', 'audio');
  const jobAssetsAudio = path.resolve(process.cwd(), 'jobs', jobId, 'assets', 'audio');

  fs.mkdirSync(jobAssetsAudio, {recursive: true});

  // Copy neutral SFX and room-tone if present
  if (fs.existsSync(defaultPackDir)) {
    const files = fs.readdirSync(defaultPackDir);
    for (const f of files) {
      const dest = path.join(jobAssetsAudio, f);
      if (!fs.existsSync(dest)) {
        fs.copyFileSync(path.join(defaultPackDir, f), dest);
      }
    }
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
