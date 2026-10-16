import {
  blurSlide,
  crossZoom,
  dreamyZoom,
  filmBurn,
  linearBlur,
  pushCut,
  linearTiming,
  springTiming,
  type TransitionPresentation,
  type TransitionTiming,
} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {wipe} from '@remotion/transitions/wipe';
import {flip} from '@remotion/transitions/flip';
import {clockWipe} from '@remotion/transitions/clock-wipe';
import {dissolve} from '@remotion/transitions/dissolve';

export interface ResolvedTransition {
  presentation: TransitionPresentation<any>;
  timing: TransitionTiming;
}

export function resolveTransition(
  transitionName: string | undefined,
  sceneIndex: number
): ResolvedTransition {
  const name = (transitionName || '').toLowerCase().replace(/[-_]/g, '');
  const alternateDir = sceneIndex % 2 === 0 ? 'from-right' : 'from-left';

  switch (name) {
    case 'fade':
      return {
        presentation: fade(),
        timing: linearTiming({durationInFrames: 10}),
      };

    case 'slide':
      return {
        presentation: slide({direction: alternateDir}),
        timing: springTiming({config: {damping: 18, stiffness: 120}}),
      };

    case 'wipe':
      return {
        presentation: wipe({direction: alternateDir}),
        timing: linearTiming({durationInFrames: 10}),
      };

    case 'flip':
      return {
        presentation: flip({direction: alternateDir}),
        timing: springTiming({config: {damping: 16, stiffness: 110}}),
      };

    case 'clock':
    case 'clockwipe':
      return {
        presentation: clockWipe({width: 1920, height: 1080}),
        timing: linearTiming({durationInFrames: 12}),
      };

    case 'dissolve':
      return {
        presentation: dissolve({}),
        timing: linearTiming({durationInFrames: 10}),
      };

    case 'crosszoom':
    case 'zoom':
      return {
        presentation: crossZoom({strength: 0.8}),
        timing: springTiming({config: {damping: 15, stiffness: 135}}),
      };

    case 'dreamyzoom':
    case 'dream':
      return {
        presentation: dreamyZoom({}),
        timing: springTiming({config: {damping: 14, stiffness: 100}}),
      };

    case 'filmburn':
    case 'burn':
      return {
        presentation: filmBurn({}),
        timing: linearTiming({durationInFrames: 10}),
      };

    case 'linearblur':
    case 'blur':
      return {
        presentation: linearBlur({}),
        timing: linearTiming({durationInFrames: 10}),
      };

    case 'pushcut':
    case 'push':
      return {
        presentation: pushCut({}),
        timing: linearTiming({durationInFrames: 8}),
      };

    case 'carouselglide':
    case 'carousel':
      return {
        presentation: slide({direction: alternateDir}),
        timing: springTiming({config: {damping: 22, stiffness: 100}}),
      };

    case 'blurslide':
    default:
      return {
        presentation: blurSlide({
          direction: alternateDir,
          blur: 8,
        }),
        timing: linearTiming({durationInFrames: 10}),
      };
  }
}
