import type {BoundingBox, CameraZoomKeyframe, TelemetryEvent} from './types';

export interface ViewportDimensions {
  width: number;
  height: number;
}

export class AutoZoomCalculator {
  /**
   * Computes the focal center of a bounding box with viewport boundary clamping
   * to guarantee the zoomed window frame never slides off the canvas.
   */
  static computeClampedCenter(
    bbox: BoundingBox,
    zoomScale: number,
    viewport: ViewportDimensions = {width: 1920, height: 1080}
  ): [number, number] {
    const rawCenterX = bbox.x + bbox.width / 2;
    const rawCenterY = bbox.y + bbox.height / 2;

    if (zoomScale <= 1.0) {
      return [viewport.width / 2, viewport.height / 2];
    }

    // Safeguard 1: Edge Boundary Clamping
    // Center_X = clamp(Center_X, W / (2*scale), W - W / (2*scale))
    const halfSpanX = viewport.width / (2 * zoomScale);
    const halfSpanY = viewport.height / (2 * zoomScale);

    const minX = halfSpanX;
    const maxX = viewport.width - halfSpanX;
    const minY = halfSpanY;
    const maxY = viewport.height - halfSpanY;

    const clampedX = Math.max(minX, Math.min(maxX, rawCenterX));
    const clampedY = Math.max(minY, Math.min(maxY, rawCenterY));

    return [Math.round(clampedX * 10) / 10, Math.round(clampedY * 10) / 10];
  }

  /**
   * Evaluates the recommended zoom scale based on element footprint.
   * Compact targets (buttons, inputs) zoom 1.85x - 2.2x; larger panels zoom 1.4x - 1.6x.
   */
  static calculateTargetZoom(bbox: BoundingBox, viewport: ViewportDimensions = {width: 1920, height: 1080}): number {
    const areaRatio = (bbox.width * bbox.height) / (viewport.width * viewport.height);
    if (areaRatio < 0.04) {
      return 2.0; // High inspection zoom for buttons / inputs
    } else if (areaRatio < 0.15) {
      return 1.65; // Moderate zoom for cards / modals
    }
    return 1.35;
  }

  /**
   * Clusters telemetry events occurring within Δt <= 2.5s and builds continuous
   * CameraZoomKeyframe tracks with overview, inspection, hold, and release states.
   */
  static generateZoomTrack(
    events: TelemetryEvent[],
    totalDurationSec: number,
    fps = 60,
    viewport: ViewportDimensions = {width: 1920, height: 1080}
  ): CameraZoomKeyframe[] {
    const tracks: CameraZoomKeyframe[] = [];
    const totalFrames = Math.round(totalDurationSec * fps);

    if (events.length === 0) {
      return [
        {
          startFrame: 0,
          endFrame: totalFrames,
          zoomScale: 1.0,
          center: [viewport.width / 2, viewport.height / 2],
          easing: 'linear',
        },
      ];
    }

    // 1. Group events into temporal clusters (Δt <= 2.5s)
    const clusters: TelemetryEvent[][] = [];
    let currentCluster: TelemetryEvent[] = [events[0]];

    for (let i = 1; i < events.length; i++) {
      const prev = events[i - 1];
      const curr = events[i];
      if (curr.timestampSec - prev.timestampSec <= 2.5) {
        currentCluster.push(curr);
      } else {
        clusters.push(currentCluster);
        currentCluster = [curr];
      }
    }
    if (currentCluster.length > 0) clusters.push(currentCluster);

    let lastEndFrame = 0;

    clusters.forEach((cluster) => {
      const firstEvent = cluster[0];
      const lastEvent = cluster[cluster.length - 1];

      const targetZoom = this.calculateTargetZoom(firstEvent.boundingBox, viewport);
      const clampedCenter = this.computeClampedCenter(firstEvent.boundingBox, targetZoom, viewport);

      const targetStartFrame = Math.max(lastEndFrame, Math.round((firstEvent.timestampSec - 0.4) * fps));
      const holdDurationFrames = Math.round(1.2 * fps); // 1.2s post-interaction hold
      const targetEndFrame = Math.round(lastEvent.timestampSec * fps) + holdDurationFrames;

      // Overview buffer before cluster if gap exists
      if (targetStartFrame > lastEndFrame) {
        tracks.push({
          startFrame: lastEndFrame,
          endFrame: targetStartFrame,
          zoomScale: 1.0,
          center: [viewport.width / 2, viewport.height / 2],
          easing: 'easeOutCubic',
        });
      }

      // Inspection state with hold
      tracks.push({
        startFrame: targetStartFrame,
        endFrame: targetEndFrame,
        zoomScale: targetZoom,
        center: clampedCenter,
        easing: 'easeInOutQuart',
      });

      lastEndFrame = targetEndFrame;
    });

    // Final overview ease-out
    if (lastEndFrame < totalFrames) {
      tracks.push({
        startFrame: lastEndFrame,
        endFrame: totalFrames,
        zoomScale: 1.0,
        center: [viewport.width / 2, viewport.height / 2],
        easing: 'easeOutCubic',
      });
    }

    return tracks;
  }
}
