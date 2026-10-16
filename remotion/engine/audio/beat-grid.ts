export interface BeatGridConfig {
  bpm: number;
  fps: number;
}

export interface VoiceBudgetResult {
  durationSec: number;
  durationFrames: number;
  maxWordCount: number;
  recommendedPacingWordsPerSec: number;
}

export class BeatGridScheduler {
  readonly framesPerBeat: number;
  readonly framesPerBar: number;
  readonly framesPerSixteenth: number;
  readonly secondsPerBar: number;

  constructor(public config: BeatGridConfig) {
    this.framesPerBeat = Math.round((60 / config.bpm) * config.fps);
    this.framesPerBar = this.framesPerBeat * 4;
    this.framesPerSixteenth = Math.max(1, Math.round(this.framesPerBeat / 4));
    this.secondsPerBar = (60 / config.bpm) * 4;
  }

  /**
   * Snaps a frame to the nearest musical subdivision.
   */
  snapFrame(frame: number, subdivision: 'bar' | 'beat' | 'sixteenth' = 'beat'): number {
    const interval =
      subdivision === 'bar'
        ? this.framesPerBar
        : subdivision === 'sixteenth'
        ? this.framesPerSixteenth
        : this.framesPerBeat;
    return Math.round(frame / interval) * interval;
  }

  /**
   * Budgets word count for an ElevenLabs voiceover window locked to integer bars.
   * Target speaking rate: ~2.0 - 2.4 words per second.
   */
  calculateVoiceBudget(bars: number, targetWordsPerSec = 2.2): VoiceBudgetResult {
    const durationSec = Math.round(bars * this.secondsPerBar * 100) / 100;
    const durationFrames = bars * this.framesPerBar;
    // Keep safety headroom of 1 word so TTS tail fade fits comfortably inside the bar
    const maxWordCount = Math.max(1, Math.floor(durationSec * targetWordsPerSec) - 1);
    return {
      durationSec,
      durationFrames,
      maxWordCount,
      recommendedPacingWordsPerSec: targetWordsPerSec,
    };
  }

  /**
   * Generates timeline beat markers for the entire composition.
   */
  generateBeatTimeline(totalFrames: number): Array<{frame: number; isDownbeat: boolean; barNumber: number}> {
    const beats: Array<{frame: number; isDownbeat: boolean; barNumber: number}> = [];
    for (let f = 0; f < totalFrames; f += this.framesPerBeat) {
      const beatIndex = Math.round(f / this.framesPerBeat);
      const isDownbeat = beatIndex % 4 === 0;
      const barNumber = Math.floor(beatIndex / 4) + 1;
      beats.push({frame: f, isDownbeat, barNumber});
    }
    return beats;
  }
}
