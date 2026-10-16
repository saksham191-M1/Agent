import type {Position3D} from '../semantic-ui/types';

export interface CameraWaypoint {
  timeSec: number;
  frame: number;
  position: Position3D; // World units
  target: Position3D;   // Point of interest [tx, ty, tz]
  rotationDeg: [number, number, number]; // [pitch, yaw, roll]
  fov: number; // Field of View (e.g. 45 degrees)
  focusDistance?: number;
  aperture?: number;
  easing?: 'agency-snap' | 'smooth-drift' | 'linear';
}

export interface CameraFlightPath {
  waypoints: CameraWaypoint[];
}
