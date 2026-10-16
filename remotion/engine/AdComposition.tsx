import React from 'react';
import {TransitionSeries} from '@remotion/transitions';
import type {AdSpec, SceneRenderer, Tokens} from './types';
import {AudioMixer} from './audio/Mixer';
import {resolveTransition} from './transitions/resolver';

export const AdComposition: React.FC<{spec: AdSpec; tokens: Tokens; renderScene: SceneRenderer}> = ({spec, tokens, renderScene: Scene}) => {
  return (
    <>
      <TransitionSeries>
        {spec.scenes.map((scene, index) => {
          const hasTransition =
            index < spec.scenes.length - 1 &&
            Boolean(scene.transitionOut && scene.transitionOut !== 'none');
          const resolved = hasTransition ? resolveTransition(scene.transitionOut, index) : null;
          const transitionFrames = resolved ? 10 : 0;
          const durationInFrames =
            Math.round(scene.duration * spec.fps) + transitionFrames;

          return (
            <React.Fragment key={scene.id}>
              <TransitionSeries.Sequence durationInFrames={durationInFrames} name={scene.id}>
                <Scene scene={scene} tokens={tokens} />
              </TransitionSeries.Sequence>
              {resolved && (
                <TransitionSeries.Transition
                  timing={resolved.timing}
                  presentation={resolved.presentation}
                />
              )}
            </React.Fragment>
          );
        })}
      </TransitionSeries>
      <AudioMixer spec={spec} />
    </>
  );
};

