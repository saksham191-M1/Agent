import type {CameraWaypoint} from './types';

export interface EffectCraftCameraProps {
  position: [number, number, number];
  pointOfInterest: [number, number, number];
  zoom: number;
}

export interface ThreeJsCameraProps {
  position: [number, number, number];
  target: [number, number, number];
  fov: number;
}

export class CameraCoordinateAdapter {
  constructor(private comp: { width: number; height: number }) {}

  toEffectCraft(wp: CameraWaypoint): EffectCraftCameraProps {
    const cx = this.comp.width / 2;
    const cy = this.comp.height / 2;

    const ecPos: [number, number, number] = [
      Math.round((cx + wp.position[0]) * 100) / 100,
      Math.round((cy - wp.position[1]) * 100) / 100, // Y inverted for AE
      Math.round(wp.position[2] * 100) / 100,
    ];

    const ecTarget: [number, number, number] = [
      Math.round((cx + wp.target[0]) * 100) / 100,
      Math.round((cy - wp.target[1]) * 100) / 100,
      Math.round(wp.target[2] * 100) / 100,
    ];

    const rad = (wp.fov * Math.PI) / 360;
    const zoom = (this.comp.height / 2) / Math.tan(rad);

    return {
      position: ecPos,
      pointOfInterest: ecTarget,
      zoom: Math.round(zoom * 10) / 10,
    };
  }

  toThreeJs(wp: CameraWaypoint): ThreeJsCameraProps {
    return {
      position: [wp.position[0], wp.position[1], wp.position[2]],
      target: [wp.target[0], wp.target[1], wp.target[2]],
      fov: wp.fov,
    };
  }
}
