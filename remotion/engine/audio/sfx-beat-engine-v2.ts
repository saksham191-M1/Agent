/**
 * AUDIO PIPELINE: SFX BEAT ENGINE v2 - UNIVERSAL
 *
 * Audio Director engine for dynamic timeline beat subdivision, 3-sound SFX vocabulary,
 * pre-peak visual synchronization (-80ms), and automated ducking/stagger calculation.
 */

export type SfxType = 'POP' | 'TICK' | 'CLICK';

export interface SfxCue {
  id: string;
  type: SfxType;
  timeSec: number;
  percentage: number;
  gain: number;
  description: string;
  duckMusicDb?: number;
  pitchVariation?: number; // e.g. 1.0, 0.97, 0.94
}

export interface BeatPartition {
  beatNumber: number;
  label: string;
  startPct: number;
  endPct: number;
  startSec: number;
  endSec: number;
  durationSec: number;
}

export interface VisualEvent {
  timeSec: number; // visual peak timestamp
  energy: 'large_scale_entrance' | 'transition_stagger' | 'human_interaction';
  description: string;
  isGridStagger?: boolean; // triggers 3x TICK at 15ms intervals
}

export class SfxBeatEngineV2 {
  /**
   * Rule 1: Dynamic Beat Calculation
   * Duration <= 15s -> 5 beats
   * Duration > 15s  -> 7 beats
   */
  static calculateBeats(durationSec: number): BeatPartition[] {
    const numBeats = durationSec <= 15 ? 5 : 7;
    const beatDuration = durationSec / numBeats;

    const labels5 = [
      'HOOK',
      'PROBLEM/PROMPT',
      'SOLUTION/FLASH',
      'PROOF/BENTO/FEATURES',
      'CTA/OUTRO',
    ];

    const labels7 = [
      'HOOK',
      'PROBLEM',
      'PROMPT/DEMO',
      'SOLUTION/FLASH',
      'PROOF/BENTO',
      'FEATURES',
      'CTA/OUTRO',
    ];

    const labels = numBeats === 5 ? labels5 : labels7;
    const partitions: BeatPartition[] = [];

    for (let i = 0; i < numBeats; i++) {
      const startPct = (i / numBeats) * 100;
      const endPct = ((i + 1) / numBeats) * 100;
      const startSec = Math.round((i * beatDuration) * 100) / 100;
      const endSec = Math.round(((i + 1) * beatDuration) * 100) / 100;

      partitions.push({
        beatNumber: i + 1,
        label: labels[i],
        startPct: Math.round(startPct * 10) / 10,
        endPct: Math.round(endPct * 10) / 10,
        startSec,
        endSec,
        durationSec: Math.round(beatDuration * 100) / 100,
      });
    }

    return partitions;
  }

  /**
   * Rule 2 & Rule 3: Universal SFX Generation & Pre-Peak Synchronization
   * Fire SFX 80ms BEFORE visual peak.
   * Ducking: Music -6dB on POP.
   * Grid stagger: 3x TICK at 15ms intervals with descending pitch.
   */
  static generateSynchronizedMap(durationSec: number, customEvents?: VisualEvent[]): {
    beats: BeatPartition[];
    cues: SfxCue[];
  } {
    const beats = this.calculateBeats(durationSec);
    const cues: SfxCue[] = [];
    const SYNC_OFFSET_SEC = 0.080; // 80ms pre-fire

    // If explicit visual events are provided, schedule from visual triggers
    if (customEvents && customEvents.length > 0) {
      customEvents.forEach((event, idx) => {
        const fireSec = Math.max(0, event.timeSec - SYNC_OFFSET_SEC);
        const pct = Math.round((fireSec / durationSec) * 1000) / 10;

        if (event.isGridStagger) {
          // 3x TICK at 15ms intervals, descending pitch
          const pitches = [1.0, 0.95, 0.90];
          for (let i = 0; i < 3; i++) {
            const staggerSec = Math.round((fireSec + i * 0.015) * 1000) / 1000;
            cues.push({
              id: `grid-tick-${idx}-${i + 1}`,
              type: 'TICK',
              timeSec: staggerSec,
              percentage: Math.round((staggerSec / durationSec) * 1000) / 10,
              gain: 0.55,
              pitchVariation: pitches[i],
              description: `${event.description} (Stagger card ${i + 1}/3)`,
            });
          }
        } else if (event.energy === 'large_scale_entrance') {
          cues.push({
            id: `pop-${idx}`,
            type: 'POP',
            timeSec: Math.round(fireSec * 100) / 100,
            percentage: pct,
            gain: 0.85,
            duckMusicDb: -6,
            description: event.description,
          });
        } else if (event.energy === 'transition_stagger') {
          cues.push({
            id: `tick-${idx}`,
            type: 'TICK',
            timeSec: Math.round(fireSec * 100) / 100,
            percentage: pct,
            gain: 0.55,
            description: event.description,
          });
        } else {
          cues.push({
            id: `click-${idx}`,
            type: 'CLICK',
            timeSec: Math.round(fireSec * 100) / 100,
            percentage: pct,
            gain: 0.70,
            pitchVariation: 1.0 + (((idx % 5) - 2) * 0.015), // +/- 3% deterministic variation
            description: event.description,
          });
        }
      });
    } else {
      // Default procedural rhythm matching beat structure
      beats.forEach((b) => {
        if (b.beatNumber === 1) {
          // Beat 1: Hook Entrance POP
          const hookFire = Math.max(0.1, Math.round((b.durationSec * 0.08) * 100) / 100);
          cues.push({
            id: 'b1-hook-pop',
            type: 'POP',
            timeSec: hookFire,
            percentage: Math.round((hookFire / durationSec) * 1000) / 10,
            gain: 0.80,
            duckMusicDb: -6,
            description: 'Entrance',
          });
          // Secondary transition tick
          const tickTime = Math.round((b.durationSec * 0.75) * 100) / 100;
          cues.push({
            id: 'b1-transition-tick',
            type: 'TICK',
            timeSec: tickTime,
            percentage: Math.round((tickTime / durationSec) * 1000) / 10,
            gain: 0.55,
            description: 'Visual lead-in',
          });
        } else if (b.label.includes('PROMPT') || b.label.includes('DEMO')) {
          // Tactile clicks for input interaction
          const clickStart = b.startSec + 0.3;
          for (let c = 0; c < 3; c++) {
            const cTime = Math.round((clickStart + c * 0.25) * 100) / 100;
            if (cTime < b.endSec) {
              cues.push({
                id: `b${b.beatNumber}-click-${c + 1}`,
                type: 'CLICK',
                timeSec: cTime,
                percentage: Math.round((cTime / durationSec) * 1000) / 10,
                gain: 0.70,
                pitchVariation: 1.0 + (c % 2 === 0 ? 0.02 : -0.02),
                description: `Tactile tap ${c + 1}`,
              });
            }
          }
        } else if (b.label.includes('BENTO') || b.label.includes('PROOF')) {
          // Grid stagger 3x TICK
          const gridBase = b.startSec + 0.2;
          const pitches = [1.0, 0.95, 0.90];
          for (let g = 0; g < 3; g++) {
            const gTime = Math.round((gridBase + g * 0.015) * 1000) / 1000;
            cues.push({
              id: `b${b.beatNumber}-grid-tick-${g + 1}`,
              type: 'TICK',
              timeSec: gTime,
              percentage: Math.round((gTime / durationSec) * 1000) / 10,
              gain: 0.60,
              pitchVariation: pitches[g],
              description: `Grid card reveal ${g + 1}/3`,
            });
          }
        } else if (b.label.includes('FLASH') || b.label.includes('SOLUTION')) {
          const popTime = Math.round((b.startSec + 0.15) * 100) / 100;
          cues.push({
            id: `b${b.beatNumber}-flash-pop`,
            type: 'POP',
            timeSec: popTime,
            percentage: Math.round((popTime / durationSec) * 1000) / 10,
            gain: 0.85,
            duckMusicDb: -6,
            description: 'Feature slam',
          });
        } else {
          // CTA Outro POP
          const ctaTime = Math.round((b.startSec + 0.2) * 100) / 100;
          cues.push({
            id: `b${b.beatNumber}-cta-pop`,
            type: 'POP',
            timeSec: ctaTime,
            percentage: Math.round((ctaTime / durationSec) * 1000) / 10,
            gain: 0.90,
            duckMusicDb: -6,
            description: 'Final logo lockup',
          });
        }
      });
    }

    cues.sort((a, b) => a.timeSec - b.timeSec);
    return {beats, cues};
  }

  /**
   * Rule 4: Mandatory Output Formatter (Dual % and Seconds tree)
   */
  static formatOutput(durationSec: number, customEvents?: VisualEvent[]): string {
    const {beats, cues} = this.generateSynchronizedMap(durationSec, customEvents);
    const lines: string[] = [];

    lines.push(`For ${durationSec.toFixed(2)}s video:`);

    beats.forEach((b) => {
      lines.push(`${b.startSec.toFixed(2)}s (${b.startPct.toFixed(1)}%) ─────────────────`);
      lines.push(`│ Beat ${b.beatNumber}: ${b.label}`);

      const beatCues = cues.filter(
        (c) => c.timeSec >= b.startSec && (b.beatNumber === beats.length ? c.timeSec <= b.endSec + 0.05 : c.timeSec < b.endSec)
      );

      beatCues.forEach((cue) => {
        const duckStr = cue.duckMusicDb ? ` [Ducking: ${cue.duckMusicDb}dB]` : '';
        const pitchStr = cue.pitchVariation ? ` [Pitch: ${cue.pitchVariation.toFixed(2)}x]` : '';
        lines.push(
          `│ ${cue.timeSec.toFixed(2)}s (${cue.percentage.toFixed(1)}%) : [${cue.type}] ${cue.description} (Gain: ${cue.gain.toFixed(2)})${duckStr}${pitchStr}`
        );
      });
    });

    lines.push(`${durationSec.toFixed(2)}s (100.0%) ───────────────── (End of Timeline)`);
    return lines.join('\n');
  }
}
