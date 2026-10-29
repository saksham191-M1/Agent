import gsap from 'gsap';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {useRef} from 'react';

export interface UseGsapTimelineOptions {
  durationInFrames?: number;
  setup: (tl: gsap.core.Timeline) => void;
  dependencies?: React.DependencyList;
}

/**
 * Remotion hook that synchronizes a GSAP timeline deterministically with Remotion frames.
 * Allows scrubbable, frame-accurate sequencing without wall-clock drift.
 */
export function useGsapTimeline(options: UseGsapTimelineOptions): {
  progress: number;
  timeline: gsap.core.Timeline;
} {
  const frame = useCurrentFrame();
  const {durationInFrames: compDuration} = useVideoConfig();
  const duration = options.durationInFrames || compDuration;

  const tlRef = useRef<gsap.core.Timeline | null>(null);

  if (!tlRef.current) {
    const tl = gsap.timeline({paused: true});
    options.setup(tl);
    tlRef.current = tl;
  }

  const progress = Math.min(1, Math.max(0, frame / duration));

  // Frame-accurate seek
  if (tlRef.current) {
    tlRef.current.progress(progress);
  }

  return {
    progress,
    timeline: tlRef.current,
  };
}
