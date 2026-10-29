/**
 * flags.ts
 * ────────
 * Central feature flags for ad generation pipeline.
 */

export const FLAGS = {
  get PIPELINE_V2(): boolean {
    return (process.env.PIPELINE_V2 === '1' || process.env.PIPELINE_V2 === 'true') as boolean;
  },
};
