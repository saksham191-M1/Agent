export interface TypewriterConfig {
  text?: string;
  startFrame?: number;
  durationFrames?: number;
  showCursor?: boolean;
}

export interface CursorConfig {
  from?: [number, number];
  to?: [number, number];
  startFrame?: number;
  clickFrame?: number;
}

export interface ReactiveTargetConfig {
  targetIndex?: number;
  triggerFrame?: number;
  activeLabel?: string;
  badgeText?: string;
  glow?: boolean;
}

export interface MetricTickerConfig {
  from: number;
  to: number;
  prefix?: string;
  suffix?: string;
  startFrame?: number;
  durationFrames?: number;
  decimals?: number;
}

export interface StateToggleConfig {
  options: string[];
  initialIndex?: number;
  toggledIndex?: number;
  switchFrame?: number;
}

export interface ToastConfig {
  message: string;
  icon?: string;
  showAtFrame?: number;
  durationFrames?: number;
  type?: 'success' | 'info' | 'alert';
}

export interface ProgressScrubberConfig {
  startFrame?: number;
  durationFrames?: number;
}

export interface InteractionSpec {
  typewriter?: TypewriterConfig | boolean;
  cursor?: CursorConfig | boolean;
  reactiveTarget?: ReactiveTargetConfig;
  ticker?: MetricTickerConfig;
  toggle?: StateToggleConfig;
  toast?: ToastConfig;
  progress?: ProgressScrubberConfig;
}
