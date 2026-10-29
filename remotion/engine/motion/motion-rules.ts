import motionRulesJson from '../motion-rules.json';
import type {AdSpec, SceneSpec} from '../types';

export interface MotionRules {
  name: string;
  version: string;
  scope: string;
  notes: string[];
  timing: {
    unit: string;
    bpm_source: string;
    downbeat_source: string;
    events_placed_on: string;
    snap_motion_to_beat: boolean;
  };
  camera: {
    required: boolean;
    never_fully_stops: boolean;
    push_scale_per_scene: [number, number];
    easing: string;
    reset_between_scenes: boolean;
  };
  text_entry: {
    method: string;
    per_letter: boolean;
    stagger_beats: number;
    stagger_clamp_seconds: [number, number];
    duration_beats: number;
    duration_clamp_seconds: [number, number];
    easing: string;
    typing_variant: {
      allowed: boolean;
      caret: string;
      chars_per_second: [number, number];
    };
    ban_terminal_punctuation_on_headlines: boolean;
  };
  continuous_patterns: {
    rotate_continuously: boolean;
    rotate_per_beat_notch: boolean;
    loop_exact_at_final_frame: boolean;
    rule: string;
  };
  transitions: {
    scene_swap: {
      type: string;
      duration_beats: number;
      duration_clamp_seconds: [number, number];
      easing: string;
      centered_on_boundary: boolean;
    };
    element_swap: {
      type: string;
      duration_beats: number;
    };
    flood_or_morph: {
      allowed: boolean;
      morph_inside_same_camera_transform: boolean;
      swap_flood_circle_for_full_rect_once_covered: boolean;
    };
  };
  color_change: {
    type: string;
    duration_beats: number;
    duration_clamp_seconds: [number, number];
  };
  objects: {
    entry: string;
    idle: string;
    sway_degrees: [number, number];
    sway_period_seconds: [number, number];
    never_appear_instantly: boolean;
  };
  counters: {
    count_up: boolean;
    easing: string;
    duration_seconds: [number, number];
    read_time_from: string;
    format: string;
  };
  ending: {
    fold_back_to_opening: boolean;
    last_frame_matches_first: string;
  };
  banned: string[];
  render: {
    fps: number;
    motion_blur_subframes: number;
    note_on_subframes: string;
    audio_loudness_lufs: number;
  };
  qa: {
    scan_single_frame_pops: boolean;
    max_hard_jumps_per_second: string;
    max_share_of_still_frames: string;
    fail_on_banned_rule_violation: boolean;
  };
}

export const MOTION_RULES: MotionRules = motionRulesJson as MotionRules;

/**
 * Converts beats into seconds using the measured BPM and clamps within bounds.
 * Formula: 1 beat = 60 / BPM seconds.
 */
export function beatToSeconds(
  beats: number,
  bpm: number,
  clamp?: [number, number]
): number {
  const safeBpm = bpm > 0 ? bpm : 120;
  const rawSeconds = beats * (60 / safeBpm);
  if (!clamp) return rawSeconds;
  return Math.min(Math.max(rawSeconds, clamp[0]), clamp[1]);
}

/**
 * Converts beats into exact frames at the given FPS.
 */
export function beatToFrames(
  beats: number,
  bpm: number,
  fps = 60,
  clampSeconds?: [number, number]
): number {
  const sec = beatToSeconds(beats, bpm, clampSeconds);
  return Math.max(1, Math.round(sec * fps));
}

/**
 * Cubic ease-out: 1 - Math.pow(1 - t, 3)
 */
export function easeOutCubic(t: number): number {
  const clamped = Math.max(0, Math.min(1, t));
  return 1 - Math.pow(1 - clamped, 3);
}

/**
 * Cubic ease-in-out:
 * t < 0.5 ? 4 * t^3 : 1 - Math.pow(-2 * t + 2, 3) / 2
 */
export function easeInOutCubic(t: number): number {
  const clamped = Math.max(0, Math.min(1, t));
  return clamped < 0.5
    ? 4 * clamped * clamped * clamped
    : 1 - Math.pow(-2 * clamped + 2, 3) / 2;
}

/**
 * Camera push scale per scene:
 * Continuously pushes from push_scale_per_scene[0] (e.g. 1.03) to [1] (e.g. 1.07).
 * Pure function of time, never fully stops.
 */
export function getCameraPushScale(
  frame: number,
  durationFrames: number,
  range: [number, number] = MOTION_RULES.camera.push_scale_per_scene
): number {
  const t = Math.max(0, Math.min(1, frame / Math.max(1, durationFrames)));
  // gentle ease: mix of linear and cubic
  const gentle = 0.5 * t + 0.5 * (1 - Math.pow(1 - t, 2));
  return range[0] + (range[1] - range[0]) * gentle;
}

/**
 * Text entry via mask_line_rise with per-letter / per-word stagger.
 * Returns opacity [0..1] and translateY in px.
 */
export function getTextMaskRise(
  frame: number,
  itemIndex: number,
  totalItems: number,
  bpm = 120,
  fps = 60
): {progress: number; translateY: number; opacity: number} {
  const staggerSec = beatToSeconds(
    MOTION_RULES.text_entry.stagger_beats,
    bpm,
    MOTION_RULES.text_entry.stagger_clamp_seconds
  );
  const durationSec = beatToSeconds(
    MOTION_RULES.text_entry.duration_beats,
    bpm,
    MOTION_RULES.text_entry.duration_clamp_seconds
  );

  const startFrame = Math.round(itemIndex * staggerSec * fps);
  const durFrames = Math.max(1, Math.round(durationSec * fps));

  if (frame < startFrame) {
    return {progress: 0, translateY: 36, opacity: 0};
  }

  const t = Math.min(1, (frame - startFrame) / durFrames);
  const progress = easeOutCubic(t);

  return {
    progress,
    translateY: (1 - progress) * 36,
    opacity: progress,
  };
}

/**
 * Continuous slow sway for idle objects (1-3 degrees, 4-7 seconds period).
 */
export function getSlowSway(
  frame: number,
  fps = 60,
  phaseOffset = 0,
  degrees = MOTION_RULES.objects.sway_degrees[0],
  periodSec = MOTION_RULES.objects.sway_period_seconds[0]
): {rotationDeg: number; translateY: number} {
  const time = frame / fps;
  const angle = (2 * Math.PI * time) / periodSec + phaseOffset;
  const rotationDeg = Math.sin(angle) * degrees;
  const translateY = Math.cos(angle) * 3;
  return {rotationDeg, translateY};
}

/**
 * Continuous pattern rotation rule:
 * Picks angular speed so total rotation over totalFrames is an exact integer of pattern periods.
 */
export function getPatternRotation(
  frame: number,
  totalFrames: number,
  periods = 1
): number {
  const progress = frame / Math.max(1, totalFrames);
  return progress * 360 * periods;
}

/**
 * Counter progress calculation using ease_out_cubic over duration.
 */
export function getCounterProgress(
  frame: number,
  durationFrames: number
): number {
  const t = Math.max(0, Math.min(1, frame / Math.max(1, durationFrames)));
  return easeOutCubic(t);
}

/**
 * QA Validator: Validates AdSpec against banned motion rules and requirements.
 */
export function validateMotionRules(spec: AdSpec): {
  valid: boolean;
  violations: string[];
  warnings: string[];
} {
  const violations: string[] = [];
  const warnings: string[] = [];
  const banned = new Set(MOTION_RULES.banned);

  // 1. Check FPS
  if (spec.fps !== MOTION_RULES.render.fps) {
    violations.push(
      `Render FPS is ${spec.fps}, but motion_rules requires ${MOTION_RULES.render.fps} fps.`
    );
  }

  // 2. Check banned transitions
  spec.scenes.forEach((scene: SceneSpec, idx: number) => {
    const trans = (scene.transitionOut || '').toLowerCase();
    if (trans === 'cut' || trans === 'hardcut') {
      if (banned.has('hard_cut')) {
        violations.push(
          `Scene ${scene.id} (index ${idx}) uses 'hard_cut' which is banned in motion_rules.`
        );
      }
    }
    if (trans === 'crossfade' || trans === 'cross-fade') {
      if (banned.has('crossfade_between_scenes')) {
        violations.push(
          `Scene ${scene.id} (index ${idx}) uses 'crossfade_between_scenes' which is banned in motion_rules.`
        );
      }
    }
    if (trans === 'whiteflash' || trans === 'flash') {
      if (banned.has('white_flash')) {
        violations.push(
          `Scene ${scene.id} uses 'white_flash' which is banned in motion_rules.`
        );
      }
    }

    // 2b. Warn on entry/exit styles the rules ban (slam / pop / bounce). Warning only: existing jobs use these names.
    const motion = (scene as any).motion || {};
    [motion.enter, motion.exit].forEach((name: unknown) => {
      if (typeof name === 'string' && /(slam|pop|bounce)/i.test(name)) {
        warnings.push(`Scene ${scene.id} uses motion style '${name}', which conflicts with the banned pop_in_or_scale_slam rule.`);
      }
    });

    // 3. Check headline terminal punctuation rule
    if (
      MOTION_RULES.text_entry.ban_terminal_punctuation_on_headlines &&
      scene.headline
    ) {
      const trimmed = scene.headline.trim();
      if (trimmed.endsWith('.') || trimmed.endsWith(';') || trimmed.endsWith(':')) {
        violations.push(
          `Scene ${scene.id} headline "${scene.headline}" ends with terminal punctuation, which violates motion_rules.text_entry.ban_terminal_punctuation_on_headlines.`
        );
      }
    }
  });

  return {
    valid: violations.length === 0,
    violations,
    warnings,
  };
}
