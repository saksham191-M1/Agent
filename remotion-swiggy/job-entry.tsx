import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {AdComposition, ProjectAdComposition, projectDimensions} from './engine';
import type {ProjectManifest} from './engine';
import {getJob} from './jobs/registry';

const dimensions = (format: string) => format === '1:1' ? {width: 1080, height: 1080} : format === '16:9' ? {width: 1920, height: 1080} : {width: 1080, height: 1920};

const JobComposition: React.FC<{jobId: string}> = ({jobId}) => {
  const job = getJob(jobId);
  return <AdComposition spec={job.spec} tokens={job.tokens} renderScene={job.renderScene} />;
};

const ProjectComposition: React.FC<{project: ProjectManifest}> = ({project}) => <ProjectAdComposition manifest={project} />;

const previewProject: ProjectManifest = {
  id: 'preview', name: 'Preview', quality: 'draft', format: '9:16', fps: 24, durationSec: 1,
  brief: {name: 'Preview', description: '', audience: '', problem: '', benefits: [], cta: 'Explore', url: '', color: '#a78bfa', template: 'spotlight', tone: 'Confident', language: 'English'},
  scenes: [{id: 'S1', kind: 'Hook', start: 0, end: 1, duration: 1, headline: 'Preview', body: '', narration: ''}], assets: {},
};

export const RemotionRoot: React.FC = () => <>
  <Composition id="Ad" component={JobComposition} defaultProps={{jobId: 'swiggy-001'}} calculateMetadata={({props}) => { const job = getJob(props.jobId); const size = dimensions(job.spec.format); return {durationInFrames: Math.round(job.spec.durationSec * job.spec.fps), fps: job.spec.fps, ...size}; }} />
  <Composition id="ProjectAd" component={ProjectComposition} defaultProps={{project: previewProject}} calculateMetadata={({props}) => { const project = props.project as ProjectManifest; const size = projectDimensions(project.format, project.quality); return {durationInFrames: Math.round(project.durationSec * project.fps), fps: project.fps, ...size}; }} />
</>;

registerRoot(RemotionRoot);
