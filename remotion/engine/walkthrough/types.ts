export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type TelemetryEventType = 'click' | 'type' | 'scroll' | 'hover' | 'navigate';

export interface TelemetryEvent {
  id: string;
  type: TelemetryEventType;
  timestampSec: number;
  selector: string;
  label?: string;
  boundingBox: BoundingBox;
  payload?: {
    typedText?: string;
    scrollDelta?: number;
  };
}

export interface WalkthroughTelemetry {
  viewport: {
    width: number;
    height: number;
    scaleFactor: number;
  };
  events: TelemetryEvent[];
}

export interface CameraZoomKeyframe {
  startFrame: number;
  endFrame: number;
  zoomScale: number;
  center: [number, number]; // [x, y] in viewport
  easing: 'easeOutCubic' | 'easeInOutQuart' | 'linear';
}

export interface CursorAction {
  startFrame: number;
  endFrame: number;
  from: [number, number];
  to: [number, number];
  clickFrame?: number;
  arcOffset?: number; // Perpendicular Bézier displacement (15px-45px)
  typingText?: string;
}

export interface FoleyMarker {
  frame: number;
  type: 'mechanical_tick' | 'tactile_pop' | 'filtered_air_whoosh' | 'keyboard_tap';
  volume: number;
}

export interface WalkthroughConfig {
  sourceRecording: string;
  cameraZoomTrack: CameraZoomKeyframe[];
  cursorTrack: CursorAction[];
  audio: {
    voiceoverTrack: string;
    duckingDb: number;
    foleyEvents: FoleyMarker[];
  };
}

export interface SoftwareWalkthroughSpec {
  version: '2.0.0';
  mode: 'software_walkthrough';
  metadata: {
    title: string;
    fps: number;
    width: number;
    height: number;
  };
  walkthroughConfig: WalkthroughConfig;
}

export interface FrameRemapEntry {
  sourceFrame: number;
  outputFrame: number;
  speedFactor: number; // 1.0 = normal, up to 4.0 = speed ramp
}
