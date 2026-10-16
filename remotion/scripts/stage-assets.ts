import {cpSync, mkdirSync, rmSync} from 'node:fs';
import {resolve} from 'node:path';

export const stageJobAssets = (root: string, jobId: string) => {
  const source = resolve(root, 'jobs', jobId, 'assets');
  const target = resolve(root, 'public', 'jobs', jobId, 'assets');
  mkdirSync(resolve(root, 'public', 'jobs', jobId), {recursive: true});
  rmSync(target, {recursive: true, force: true});
  cpSync(source, target, {recursive: true});
};
