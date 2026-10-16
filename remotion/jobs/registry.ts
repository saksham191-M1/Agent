import type {AdSpec, BrandJson, SceneRenderer, Tokens} from '../engine';
import {loadTokens} from '../engine';
import {generatedJobs} from './registry.generated';

type JobDefinition = {id: string; brand: BrandJson; spec: AdSpec; renderScene: SceneRenderer};
type ResolvedJob = JobDefinition & {tokens: Tokens};

const jobs: Record<string, JobDefinition> = generatedJobs;

const tokenCache = new Map<string, Tokens>();

export const getJob = (id: string): ResolvedJob => {
  const job = jobs[id];
  if (!job) throw new Error(`Unknown job: ${id}. Available jobs: ${listJobs().join(', ')}`);
  const tokens = tokenCache.get(id) ?? loadTokens(job.brand, job.spec.format);
  tokenCache.set(id, tokens);
  return {...job, tokens};
};

export const listJobs = (): string[] => Object.keys(jobs);
