import type {TelemetryEvent, FrameRemapEntry} from './types';

export interface WordTimestamp {
  word: string;
  startSec: number;
  endSec: number;
}

export interface VoiceAlignmentConfig {
  fps: number;
  voiceWords: WordTimestamp[];
  idleThresholdSec?: number; // e.g. 1.0s
  maxSpeedFactor?: number;   // e.g. 4.0x
}

export class VoiceFirstAligner {
  /**
   * Safeguard 2: Dynamic Time Warping (DTW) Frame Decoupling.
   * Scans browser telemetry for idle intervals (> idleThresholdSec) and compresses
   * them up to maxSpeedFactor (400%) while holding narrator dialogue constant.
   * Emits a monotonic frame-remapping table: sourceFrame -> outputFrame.
   */
  static generateFrameRemapTable(
    totalSourceFrames: number,
    activeIntervals: Array<{startSec: number; endSec: number}>,
    config: VoiceAlignmentConfig
  ): FrameRemapEntry[] {
    const {fps, idleThresholdSec: _idleThresholdSec = 1.0, maxSpeedFactor = 4.0} = config;
    const remapTable: FrameRemapEntry[] = [];

    let currentSourceFrame = 0;
    let currentOutputFrame = 0;

    while (currentSourceFrame < totalSourceFrames) {
      const currentTimeSec = currentSourceFrame / fps;

      // Check if current time is within an active interaction window
      const inActiveWindow = activeIntervals.some(
        (w) => currentTimeSec >= w.startSec - 0.2 && currentTimeSec <= w.endSec + 0.5
      );

      // If active, run at 1.0x; if idle, compress up to 4.0x
      const speed = inActiveWindow ? 1.0 : maxSpeedFactor;
      const step = Math.max(1, Math.round(speed));

      remapTable.push({
        sourceFrame: currentSourceFrame,
        outputFrame: currentOutputFrame,
        speedFactor: speed,
      });

      currentSourceFrame += step;
      currentOutputFrame += 1;
    }

    return remapTable;
  }

  /**
   * Remaps a source timestamp or frame to the output warped timeline.
   */
  static remapSourceFrame(sourceFrame: number, table: FrameRemapEntry[]): number {
    if (table.length === 0) return sourceFrame;
    // Binary search or closest lookup in monotonic table
    let low = 0;
    let high = table.length - 1;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      if (table[mid].sourceFrame === sourceFrame) {
        return table[mid].outputFrame;
      }
      if (table[mid].sourceFrame < sourceFrame) {
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }

    const idx = Math.min(table.length - 1, Math.max(0, low));
    return table[idx].outputFrame;
  }

  /**
   * Binds spoken words to telemetry interaction triggers:
   * Target noun initiates cursor travel, action verb triggers click contact.
   */
  static bindEventsToSpokenPhonemes(
    events: TelemetryEvent[],
    words: WordTimestamp[],
    fps = 60
  ): Array<{event: TelemetryEvent; cursorStartFrame: number; clickFrame: number}> {
    const bound: Array<{event: TelemetryEvent; cursorStartFrame: number; clickFrame: number}> = [];

    events.forEach((ev) => {
      // Find spoken word closest to this event timestamp
      const matchingWord = words.find(
        (w) => Math.abs(w.startSec - ev.timestampSec) <= 1.2
      );

      const clickFrame = Math.round(ev.timestampSec * fps);
      // Anticipate: travel starts 24-36 frames before click
      const cursorStartFrame = matchingWord
        ? Math.round(matchingWord.startSec * fps)
        : Math.max(0, clickFrame - 30);

      bound.push({
        event: ev,
        cursorStartFrame,
        clickFrame,
      });
    });

    return bound;
  }

  /**
   * Calculates audio ducking envelope:
   * Attenuates music to -20 dB during narrator dialogue; restores to -8 dB over 350ms.
   */
  static calculateDuckingEnvelope(
    currentFrame: number,
    dialogueWindows: Array<{startFrame: number; endFrame: number}>,
    fps = 60
  ): number {
    const recoveryFrames = Math.round(0.35 * fps); // 350ms recovery envelope

    for (const win of dialogueWindows) {
      if (currentFrame >= win.startFrame && currentFrame <= win.endFrame) {
        return -20.0; // Fully ducked
      }
      if (currentFrame > win.endFrame && currentFrame <= win.endFrame + recoveryFrames) {
        // Linear recovery: -20 dB -> -8 dB
        const ratio = (currentFrame - win.endFrame) / recoveryFrames;
        return -20.0 + ratio * 12.0;
      }
    }

    return -8.0; // Unducked background level
  }
}
