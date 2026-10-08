import React from 'react';
import {TransitionSeries, blurSlide, linearTiming} from '@remotion/transitions';
import type {AdSpec, SceneRenderer, Tokens} from './types';
import {AudioMixer} from './audio/Mixer';

export const AdComposition: React.FC<{spec: AdSpec; tokens: Tokens; renderScene: SceneRenderer}> = ({spec, tokens, renderScene: Scene}) => <>
  <TransitionSeries>{spec.scenes.map((scene, index) => <React.Fragment key={scene.id}><TransitionSeries.Sequence durationInFrames={Math.round(scene.duration * spec.fps) + (index < spec.scenes.length - 1 ? 10 : 0)} name={scene.id}><Scene scene={scene} tokens={tokens} /></TransitionSeries.Sequence>{index < spec.scenes.length - 1 && <TransitionSeries.Transition timing={linearTiming({durationInFrames: 10})} presentation={blurSlide({direction: index % 2 === 0 ? 'from-right' : 'from-left', blur: 8})} />}</React.Fragment>)}</TransitionSeries>
  <AudioMixer spec={spec} />
</>;
