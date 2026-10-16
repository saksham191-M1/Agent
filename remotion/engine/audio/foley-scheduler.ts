import type {CameraWaypoint} from '../stage/types';
import type {VectorNode} from '../semantic-ui/types';
import {SAAS_BEATS_T, BEAT_RENDER_MODE, tToFrames} from '../motion/physics';

export type FoleyType = 'whoosh' | 'hit' | 'ui-pop';

export interface FoleyCue {
  id: string;
  type: FoleyType;
  frame: number;
  volume: number;
  description?: string;
}

/**
 * Generates procedural foley cues synchronized to the story beats and render mode.
 * In 2.5D montage mode, schedules pre-whooshes and high-impact cut-hits on beat boundaries.
 * In 3D flight mode, schedules wider camera flight sweeps.
 */
export function generateProceduralFoley(durationInFrames: number): FoleyCue[] {
  const cues: FoleyCue[] = [];

  SAAS_BEATS_T.forEach((beat, index) => {
    const beatStartFrame = tToFrames(beat.tStart, durationInFrames);
    const renderMode = BEAT_RENDER_MODE[beat.id as keyof typeof BEAT_RENDER_MODE] || 'montage';

    // 1. Entrance Hit (Beat 1)
    if (index === 0) {
      cues.push({
        id: `${beat.id}-start`,
        type: 'hit',
        frame: 0,
        volume: 1.0,
        description: `Entrance slam: ${beat.id}`,
      });
      return;
    }

    // 2. Beat Transitions
    if (renderMode === 'montage') {
      // 2.5D Hard Cuts: Sharp pre-whoosh and heavy impact on the frame cut
      cues.push({
        id: `${beat.id}-pre-whoosh`,
        type: 'whoosh',
        frame: Math.max(0, beatStartFrame - 8),
        volume: 0.85,
        description: `Pre-cut whip whoosh: ${beat.id}`,
      });
      cues.push({
        id: `${beat.id}-cut-hit`,
        type: 'hit',
        frame: beatStartFrame,
        volume: 0.95,
        description: `Cut impact hit: ${beat.id}`,
      });
    } else {
      // 3D Flight: Longer, smoother transition sweep
      cues.push({
        id: `${beat.id}-sweep`,
        type: 'whoosh',
        frame: Math.max(0, beatStartFrame - 15),
        volume: 0.5,
        description: `3D camera flight sweep: ${beat.id}`,
      });
    }
  });

  return cues;
}

export interface FoleyEvent {
  frame: number;
  timeSec: number;
  type: 'mechanical_tick' | 'tactile_pop' | 'filtered_air_whoosh' | 'gear_rattle';
  gain: number;
  description: string;
}

export interface FoleySchedulerInput {
  fps: number;
  waypoints?: CameraWaypoint[];
  nodes?: VectorNode[];
  cursorClicks?: Array<{frame: number; description?: string}>;
}

export class FoleyScheduler {
  static scheduleEvents(input: FoleySchedulerInput): FoleyEvent[] {
    const events: FoleyEvent[] = [];
    const {fps, waypoints, nodes, cursorClicks} = input;

    // 1. Camera Velocity Peak Foley (whoosh during rapid pan/sweep)
    if (waypoints && waypoints.length > 1) {
      for (let i = 0; i < waypoints.length - 1; i++) {
        const wp1 = waypoints[i];
        const wp2 = waypoints[i + 1];
        const dx = wp2.position[0] - wp1.position[0];
        const dy = wp2.position[1] - wp1.position[1];
        const dz = wp2.position[2] - wp1.position[2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        // If camera travels significant distance (> 400px), trigger whoosh at midpoint
        if (dist > 400) {
          const midFrame = Math.round((wp1.frame + wp2.frame) / 2);
          events.push({
            frame: midFrame,
            timeSec: Math.round((midFrame / fps) * 100) / 100,
            type: 'filtered_air_whoosh',
            gain: Math.min(0.7, 0.3 + dist / 3000),
            description: `Camera sweep: waypoint ${i} -> ${i + 1}`,
          });
        }
      }
    }

    // 2. Cursor Click Foley (tactile mechanical click)
    if (cursorClicks) {
      for (const click of cursorClicks) {
        events.push({
          frame: click.frame,
          timeSec: Math.round((click.frame / fps) * 100) / 100,
          type: 'mechanical_tick',
          gain: 0.65,
          description: click.description || 'Cursor click',
        });
      }
    }

    // 3. Node Entrance Foley
    if (nodes) {
      for (const node of nodes) {
        if (node.type === 'metric_card') {
          events.push({
            frame: 15, // standard entrance
            timeSec: 0.5,
            type: 'gear_rattle',
            gain: 0.4,
            description: `Counter roll: ${node.id}`,
          });
        } else if (node.type === 'bento_grid' || node.type === 'pill_tag') {
          events.push({
            frame: 20,
            timeSec: Math.round((20 / fps) * 100) / 100,
            type: 'tactile_pop',
            gain: 0.5,
            description: `Card pop: ${node.id}`,
          });
        }
      }
    }

    // Sort by frame
    return events.sort((a, b) => a.frame - b.frame);
  }
}
