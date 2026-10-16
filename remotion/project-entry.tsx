import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {ProjectAdComposition} from './engine/ProjectAdComposition';
import {projectDimensions} from './engine/project-types';
import type {ProjectManifest} from './engine/project-types';

const preview: ProjectManifest = {
  id: 'preview', name: 'Your product', quality: 'draft', format: '9:16', fps: 24, durationSec: 15,
  brief: {name: 'Your product', description: '', audience: '', problem: '', benefits: ['Your approved benefit'], cta: 'Explore', url: '', color: '#a78bfa', template: 'spotlight', tone: 'Confident', language: 'English'},
  scenes: [{id: 'S1', kind: 'Hook', start: 0, end: 15, duration: 15, headline: 'Your product story', body: '', narration: ''}], assets: {},
};
const Root: React.FC = () => <Composition id="ProjectAd" component={ProjectAdComposition} defaultProps={{manifest: preview}} calculateMetadata={({props}) => ({...projectDimensions(props.manifest.format, props.manifest.quality), durationInFrames: Math.round(props.manifest.durationSec * props.manifest.fps), fps: props.manifest.fps})} />;
registerRoot(Root);
