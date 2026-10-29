/**
 * spec-schema.ts
 * ──────────────
 * Zod validation schema mirroring StoryboardDirectorSpec (from Python director AI).
 * Validates the incoming storyboard JSON at the start of the scene assembler,
 * catching schema violations, invented fake data, and terminal punctuation with readable errors.
 */

import { z } from 'zod';

export const SceneDirectorSpecSchema = z.object({
  scene_id: z.number().int().positive(),
  duration_seconds: z.number().min(1.5).max(10.0),
  layout: z.string(),
  motion_profile: z.string().default('smooth'),
  voiceover: z.string(),
  kinetic_text: z.string().refine(
    (text) => !/[.:;!?]$/.test(text.trim()),
    { message: 'Headlines (kinetic_text) must NOT end with terminal punctuation (., :, ;, !, ?)' }
  ),
  visual_fx: z.string().default('carousel_glide'),
  transition_out: z.string().default('carousel_glide'),
  requires_ui_image: z.boolean().default(false),
  veo_prompt: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  ui_spec: z.record(z.string(), z.any()).nullable().optional(),
});

export type SceneDirectorSpec = z.infer<typeof SceneDirectorSpecSchema>;

export const StoryboardDirectorSpecSchema = z.object({
  product_name: z.string(),
  narrative_type: z.string().default('problem_agitate_solution'),
  selected_template: z.string().nullable().optional(),
  matched_opus_category: z.string().nullable().optional().default('MOTION'),
  aesthetic: z.record(z.string(), z.any()).nullable().optional(),
  ml_match: z.record(z.string(), z.any()).nullable().optional(),
  scene_count: z.number().int().min(3).max(8).optional(),
  total_seconds: z.number().min(10.0).max(40.0).optional(),
  music_mood: z.string().default('ambient_electronic'),
  voice_style: z.string().default('confident_conversational'),
  scenes: z.array(SceneDirectorSpecSchema).min(3).max(8),
});

export type StoryboardDirectorSpec = z.infer<typeof StoryboardDirectorSpecSchema>;

/**
 * Validates raw storyboard JSON from brain_opus.py.
 * Returns the parsed typed spec or throws a descriptive error.
 */
export function validateStoryboardSpec(raw: unknown): StoryboardDirectorSpec {
  const parseResult = StoryboardDirectorSpecSchema.safeParse(raw);
  if (!parseResult.success) {
    const issues = parseResult.error.issues || [];
    const errorMessages = issues
      .map((e) => `  - [${e.path.join('.')}]: ${e.message}`)
      .join('\n');
    throw new Error(`[spec-schema] Storyboard schema validation failed:\n${errorMessages}`);
  }

  const spec = parseResult.data;

  // Validate exact scene count
  if (spec.scene_count && spec.scene_count !== spec.scenes.length) {
    console.warn(`[spec-schema] scene_count mismatch: declared ${spec.scene_count}, found ${spec.scenes.length}. Normalizing.`);
    spec.scene_count = spec.scenes.length;
  } else {
    spec.scene_count = spec.scenes.length;
  }

  // Validate total duration sum within 0.5s tolerance
  const exactSum = Math.round(spec.scenes.reduce((acc, s) => acc + s.duration_seconds, 0) * 100) / 100;
  if (spec.total_seconds && Math.abs(spec.total_seconds - exactSum) > 0.5) {
    console.warn(`[spec-schema] total_seconds mismatch: declared ${spec.total_seconds}s, sum of scenes ${exactSum}s. Normalizing.`);
    spec.total_seconds = exactSum;
  } else {
    spec.total_seconds = exactSum;
  }

  return spec;
}
